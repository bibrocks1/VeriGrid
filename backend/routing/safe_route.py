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
from geoalchemy2.shape import to_shape
from shapely.geometry import LineString, Point
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import HazardCluster, ClusterStatus
from adapters.routing_adapter import get_route_alternatives, RoutingAPIError

HAZARD_BUFFER_METERS = 200
# Rough degrees-per-meter at mid latitudes; fine for a demo-scale buffer
# check, not for high-precision routing.
METERS_TO_DEGREES = 1 / 111_000


def _get_verified_hazard_points(db: Session) -> list[tuple[float, float, int]]:
    clusters = db.execute(
        select(HazardCluster).where(HazardCluster.status == ClusterStatus.verified)
    ).scalars().all()

    points = []
    for cluster in clusters:
        shape = to_shape(cluster.geom)
        points.append((shape.y, shape.x, cluster.id))  # (lat, lon, id)
    return points


def _route_intersects_hazards(route_latlon: list[list[float]], hazard_points) -> list[int]:
    """Returns the list of hazard cluster IDs this route passes within
    HAZARD_BUFFER_METERS of."""
    line = LineString([(lon, lat) for lat, lon in route_latlon])  # shapely wants (x, y) = (lon, lat)
    buffer_deg = HAZARD_BUFFER_METERS * METERS_TO_DEGREES

    hit_ids = []
    for lat, lon, cluster_id in hazard_points:
        hazard_point = Point(lon, lat)
        if line.distance(hazard_point) <= buffer_deg:
            hit_ids.append(cluster_id)
    return hit_ids


def get_safe_route(
    db: Session,
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
) -> dict:
    """
    Returns:
        {
            "geometry": [[lat, lon], ...],
            "distance_m": float,
            "duration_s": float,
            "avoided_hazard_ids": [...],   # hazards this route clears
            "warning": str | None,          # set if no clean alternative existed
        }
    """
    try:
        alternatives = get_route_alternatives(origin_lat, origin_lon, dest_lat, dest_lon)
    except RoutingAPIError:
        raise

    hazard_points = _get_verified_hazard_points(db)
    if not hazard_points:
        # No verified hazards at all — the default route is safe by definition.
        route = alternatives[0]
        return {**route, "avoided_hazard_ids": [], "warning": None}

    for route in alternatives:
        hits = _route_intersects_hazards(route["geometry"], hazard_points)
        if not hits:
            return {**route, "avoided_hazard_ids": [], "warning": None}

    # No clean alternative — return the shortest option and say so honestly
    # rather than silently picking one and implying it's hazard-free.
    fallback = alternatives[0]
    hits = _route_intersects_hazards(fallback["geometry"], hazard_points)
    return {
        **fallback,
        "avoided_hazard_ids": [],
        "warning": (
            f"No available route avoids all verified hazards. "
            f"This route passes near cluster(s): {hits}."
        ),
    }
