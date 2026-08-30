"""
OPTIONAL (Day 10) — flagged cuttable in the Day 10 plan.

Picks the first route alternative that doesn't pass through a buffered
verified-hazard zone. This is NOT true avoid-polygon routing (the
routing engine itself knows nothing about hazards) — it's a
select-among-alternatives heuristic: ask the routing adapter for a few
different route options, geometrically check each against known hazard
buffers, and return the first clean one, or the shortest option with a
clear warning if all of them pass through a hazard zone.
"""
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import LineString
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import HazardCluster, ClusterStatus
from adapters.routing_adapter import get_route_alternatives

HAZARD_BUFFER_METERS = 200


def _hazards_near_route(db: Session, geometry_latlng: list[list[float]], buffer_m: float) -> list[dict]:
    """Real PostGIS ST_DWithin against the Geography columns — returns
    real meters, unlike a raw shapely-degrees distance check (which
    distorts away from the equator and was the previous version's
    approach here)."""
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
            "warning": str | None,   # set if no alternative fully avoided every hazard
        }
    """
    alternatives = get_route_alternatives(origin_lat, origin_lon, dest_lat, dest_lon)

    for route in alternatives:
        hazards = _hazards_near_route(db, route["geometry"], HAZARD_BUFFER_METERS)
        if not hazards:
            return {
                "geometry": route["geometry"],
                "distanceM": route["distance_m"],
                "durationS": route["duration_s"],
                "steps": route["steps"],
                "hazardWarnings": [],
                "warning": None,
            }

    # No alternative avoided every hazard — return the shortest option and
    # say so honestly rather than silently picking one that isn't clean.
    fallback = alternatives[0]
    hazards = _hazards_near_route(db, fallback["geometry"], HAZARD_BUFFER_METERS)
    return {
        "geometry": fallback["geometry"],
        "distanceM": fallback["distance_m"],
        "durationS": fallback["duration_s"],
        "steps": fallback["steps"],
        "hazardWarnings": hazards,
        "warning": "No available route avoids all verified hazards.",
    }
