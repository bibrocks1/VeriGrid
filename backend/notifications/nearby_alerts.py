"""
OPTIONAL (Day 10) — flagged cuttable in the Day 10 plan.

Polling-based nearby-hazard alerts, chosen over WebSockets deliberately:
a WebSocket connection registry, broadcast-on-verify hook, and
reconnect/heartbeat handling is a genuinely separate subsystem and a
realistic scope risk for one day. Polling is a legitimate, much simpler
alternative for a hackathon demo — the frontend calls this on an
interval (e.g. every 15-30s) while the map is open, and diffs
client-side against what it last saw.

This is intentionally just a thin wrapper around the same nearby-cluster
query pattern already used elsewhere (retrieve_context, /reports/nearby)
so there's no new query logic to get wrong — only VERIFIED clusters are
returned, since "candidate"/"forming" clusters aren't confirmed hazards
yet and alerting on them would be noisy/premature.
"""
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models import HazardCluster, ClusterStatus


def get_nearby_verified_clusters(db: Session, lat: float, lon: float, radius_m: float = 3000) -> list[dict]:
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    rows = db.execute(
        select(HazardCluster)
        .where(HazardCluster.status == ClusterStatus.verified)
        .where(func.ST_DWithin(HazardCluster.geom, point, radius_m))
        .order_by(HazardCluster.confidence.desc())
    ).scalars().all()

    alerts = []
    for cluster in rows:
        shape = to_shape(cluster.geom)
        distance_m = _approx_distance_m(lat, lon, shape.y, shape.x)
        alerts.append({
            "cluster_id": cluster.id,
            "category": cluster.category.value if hasattr(cluster.category, "value") else str(cluster.category),
            "severity": cluster.severity,
            "explanation": cluster.explanation,
            "recommended_action": cluster.recommended_action,
            "lat": shape.y,
            "lon": shape.x,
            "distance_m": round(distance_m),
        })
    return alerts


def _approx_distance_m(lat1, lon1, lat2, lon2) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))
