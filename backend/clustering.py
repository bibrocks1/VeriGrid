from math import atan2, cos, radians, sin, sqrt

import numpy as np
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session

from consensus import recompute_confidence
from models import HazardCluster, Report, ReportCategory

EARTH_RADIUS_METERS = 6371000

# 150m radius, converted to radians for haversine distance on a unit sphere.
EPS_METERS = 150
EPS_RADIANS = EPS_METERS / EARTH_RADIUS_METERS
MIN_SAMPLES = 3

# How close a new cluster's centroid must be to an existing cluster's to be
# treated as "the same cluster" rather than a new one — reuses the same
# 150m radius as the clustering itself, checked via real haversine distance
# (not a naive degree-difference, which distorts away from the equator).
CENTROID_MATCH_METERS = EPS_METERS


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * atan2(sqrt(a), sqrt(1 - a))


def recompute_clusters_for_category(db: Session, category: ReportCategory) -> list[HazardCluster]:
    """Re-run DBSCAN over every report of `category` and upsert clusters.

    Recomputes from scratch each time rather than incrementally — simplest
    correct approach at this scale, and it self-heals if reports move
    between clusters as new data arrives.
    """
    reports = db.query(Report).filter(Report.category == category).all()

    if len(reports) < MIN_SAMPLES:
        for report in reports:
            report.cluster_id = None
        db.flush()
        _prune_empty_clusters(db, category)
        db.commit()
        return []

    points = [to_shape(r.geom) for r in reports]
    coords_radians = np.radians([[p.y, p.x] for p in points])  # [lat, lon]

    labels = DBSCAN(eps=EPS_RADIANS, min_samples=MIN_SAMPLES, metric="haversine").fit_predict(
        coords_radians
    )

    groups: dict[int, list[Report]] = {}
    for report, label in zip(reports, labels):
        if label == -1:
            report.cluster_id = None
            continue
        groups.setdefault(label, []).append(report)

    existing_clusters = db.query(HazardCluster).filter(HazardCluster.category == category).all()
    matched_ids: set[int] = set()
    touched_clusters: list[HazardCluster] = []

    for member_reports in groups.values():
        member_points = [to_shape(r.geom) for r in member_reports]
        centroid_lat = sum(p.y for p in member_points) / len(member_points)
        centroid_lng = sum(p.x for p in member_points) / len(member_points)

        cluster = _find_matching_cluster(
            existing_clusters, matched_ids, centroid_lat, centroid_lng
        )
        centroid_geom = from_shape(Point(centroid_lng, centroid_lat), srid=4326)
        if cluster is None:
            # geom is NOT NULL — must be set before the insert, not after.
            cluster = HazardCluster(
                category=category, geom=centroid_geom, confidence=0, report_count=0
            )
            db.add(cluster)
            db.flush()  # assign an id so reports can reference it below
        else:
            cluster.geom = centroid_geom

        matched_ids.add(cluster.id)
        for report in member_reports:
            report.cluster_id = cluster.id

        touched_clusters.append(cluster)

    # _prune_empty_clusters below queries membership via a DB-side subquery
    # (~HazardCluster.reports.any()), so the report.cluster_id reassignments
    # above must actually be flushed first or it sees stale membership.
    db.flush()

    for cluster in touched_clusters:
        recompute_confidence(db, cluster)

    _prune_empty_clusters(db, category)
    db.commit()
    for cluster in touched_clusters:
        db.refresh(cluster)
    return touched_clusters


def _find_matching_cluster(
    existing_clusters: list[HazardCluster],
    already_matched: set[int],
    centroid_lat: float,
    centroid_lng: float,
) -> HazardCluster | None:
    for cluster in existing_clusters:
        if cluster.id in already_matched:
            continue
        point = to_shape(cluster.geom)
        if haversine_m(point.y, point.x, centroid_lat, centroid_lng) <= CENTROID_MATCH_METERS:
            return cluster
    return None


def _prune_empty_clusters(db: Session, category: ReportCategory) -> None:
    """Delete clusters of `category` that no longer have any member reports
    (e.g. a cluster split apart and its reports moved elsewhere)."""
    empty = (
        db.query(HazardCluster)
        .filter(HazardCluster.category == category)
        .filter(~HazardCluster.reports.any())
        .all()
    )
    for cluster in empty:
        db.delete(cluster)
