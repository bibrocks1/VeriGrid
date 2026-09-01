"""
Day 10: hazard-aware routing.

Two layers, tried in order:
1. Ask OSRM for a few alternative routes and check each against verified
   hazard buffers with a real PostGIS query; return the first clean one.
2. If none of OSRM's own alternatives are clean, actively nudge around
   the hazard: compute a waypoint offset perpendicular to the route at
   the hazard's nearest point, outside the buffer, and ask OSRM for a
   fresh route forced through it (per the Day 10 plan's "insert an
   intermediate waypoint... and recalculate"). Tried on both sides of the
   route; the first side that clears every hazard wins.

Only if neither layer produces a clean route does this fall back to the
shortest option with an explicit warning, rather than silently
presenting a route that still passes through a hazard.
"""
from math import cos, radians

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import LineString, Point
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import HazardCluster, ClusterStatus
from adapters.routing_adapter import get_route_alternatives, get_route_via_waypoint

HAZARD_BUFFER_METERS = 200
# How far outside the buffer to place a nudge waypoint — buffer plus a
# safety margin so the new route doesn't just graze the edge of it.
NUDGE_OFFSET_METERS = HAZARD_BUFFER_METERS + 150
METERS_PER_DEGREE_LAT = 111_320


def _hazards_near_route(db: Session, geometry_latlng: list[list[float]], buffer_m: float) -> list[dict]:
    """Real PostGIS ST_DWithin against the Geography columns — returns
    real meters, unlike a raw shapely-degrees distance check (which
    distorts away from the equator)."""
    if len(geometry_latlng) < 2:
        return []

    line = LineString([(lng, lat) for lat, lng in geometry_latlng])
    route_line = from_shape(line, srid=4326)
    distance = func.ST_Distance(HazardCluster.geom, route_line)

    rows = (
        db.query(HazardCluster, distance)
        .filter(HazardCluster.status == ClusterStatus.verified)
        .filter(func.ST_DWithin(HazardCluster.geom, route_line, buffer_m))
        .order_by(distance)
        .all()
    )

    warnings = []
    for cluster, distance_m in rows:
        point = to_shape(cluster.geom)
        warnings.append(
            {
                "clusterId": cluster.id,
                "category": cluster.category.value,
                "lat": point.y,
                "lng": point.x,
                "distanceM": round(distance_m, 1),
                "confidence": cluster.confidence,
            }
        )
    return warnings


def _nudge_waypoints(
    geometry_latlng: list[list[float]], hazard_lat: float, hazard_lng: float, offset_m: float
) -> list[tuple[float, float]]:
    """Computes a waypoint on each side of the route, offset perpendicular
    to the route's local direction at the point nearest the hazard, by
    `offset_m`. Returns both candidates — caller tries each and keeps
    whichever produces a clean route."""
    line = LineString([(lng, lat) for lat, lng in geometry_latlng])
    hazard_point = Point(hazard_lng, hazard_lat)

    dist_along = line.project(hazard_point)
    # Two nearby points along the line to estimate the local heading.
    step = max(line.length * 0.01, 1e-6)
    ahead = line.interpolate(min(dist_along + step, line.length))
    behind = line.interpolate(max(dist_along - step, 0))
    dx, dy = ahead.x - behind.x, ahead.y - behind.y
    length = (dx**2 + dy**2) ** 0.5
    if length == 0:
        return []
    perp_x, perp_y = -dy / length, dx / length  # rotate 90°

    meters_per_degree_lng = METERS_PER_DEGREE_LAT * cos(radians(hazard_lat)) or METERS_PER_DEGREE_LAT
    offset_lat = offset_m / METERS_PER_DEGREE_LAT
    offset_lng = offset_m / meters_per_degree_lng

    waypoints = []
    for side in (1, -1):
        waypoint_lng = hazard_lng + perp_x * offset_lng * side
        waypoint_lat = hazard_lat + perp_y * offset_lat * side
        waypoints.append((waypoint_lat, waypoint_lng))
    return waypoints


def _try_detour(db: Session, origin_lat, origin_lon, dest_lat, dest_lon, geometry_latlng, hazards):
    """Attempts an actual detour around the nearest hazard blocking the
    given route. A single perpendicular offset often isn't enough to move
    a real road-network route away from the hazard (OSRM snaps the
    waypoint to the nearest road, which can loop right back), so this
    tries progressively larger offsets on both sides before giving up.
    Returns a clean route dict, or None if nothing tried clears every
    hazard."""
    nearest_hazard = hazards[0]
    for multiplier in (1, 2, 3):
        offset_m = NUDGE_OFFSET_METERS * multiplier
        for waypoint_lat, waypoint_lng in _nudge_waypoints(
            geometry_latlng, nearest_hazard["lat"], nearest_hazard["lng"], offset_m
        ):
            try:
                detoured = get_route_via_waypoint(
                    origin_lat, origin_lon, waypoint_lat, waypoint_lng, dest_lat, dest_lon
                )
            except Exception:
                continue
            if not _hazards_near_route(db, detoured["geometry"], HAZARD_BUFFER_METERS):
                return detoured
    return None


def get_safe_route(
    db: Session,
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
) -> dict:
    """
    Returns (camelCase — this is returned directly by main.py's
    /route/safe, matching what RoutePlanner.jsx on the frontend expects):
        {
            "geometry": [[lat, lng], ...],
            "distanceM": float,
            "durationS": float,
            "steps": [{"instruction": str, "distanceM": float, "durationS": float}, ...],
            "hazardWarnings": [{"clusterId", "category", "lat", "lng", "distanceM", "confidence"}, ...],
            "detoured": bool,        # true if a waypoint nudge was needed
            "warning": str | None,   # set only if nothing avoided every hazard
        }
    """
    alternatives = get_route_alternatives(origin_lat, origin_lon, dest_lat, dest_lon)

    hazards_per_alternative = []
    for route in alternatives:
        hazards = _hazards_near_route(db, route["geometry"], HAZARD_BUFFER_METERS)
        hazards_per_alternative.append(hazards)
        if not hazards:
            return {
                "geometry": route["geometry"],
                "distanceM": route["distance_m"],
                "durationS": route["duration_s"],
                "steps": route["steps"],
                "hazardWarnings": [],
                "detoured": False,
                "warning": None,
            }

    # None of OSRM's own alternatives were clean — actively try to route
    # around the nearest hazard on the shortest one rather than giving up.
    # Reuses the hazard check already done for it above instead of
    # querying the same route a second time.
    shortest = alternatives[0]
    shortest_hazards = hazards_per_alternative[0]
    detoured = _try_detour(db, origin_lat, origin_lon, dest_lat, dest_lon, shortest["geometry"], shortest_hazards)
    if detoured is not None:
        return {
            "geometry": detoured["geometry"],
            "distanceM": detoured["distance_m"],
            "durationS": detoured["duration_s"],
            "steps": detoured["steps"],
            "hazardWarnings": [],
            "detoured": True,
            "warning": None,
        }

    # Still nothing clean — return the shortest option and say so honestly
    # rather than silently presenting a route that passes through a hazard.
    return {
        "geometry": shortest["geometry"],
        "distanceM": shortest["distance_m"],
        "durationS": shortest["duration_s"],
        "steps": shortest["steps"],
        "hazardWarnings": shortest_hazards,
        "detoured": False,
        "warning": "No available route avoids all verified hazards.",
    }
