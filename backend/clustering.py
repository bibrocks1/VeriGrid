from math import radians, sin, cos, sqrt, atan2
from sklearn.cluster import DBSCAN
import numpy as np
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Report, HazardCluster, ClusterStatus

EPS_METERS = 150
EPS_RAD = EPS_METERS / 6371000
MIN_SAMPLES = 3


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def run_clustering_for_category(db: Session, category: str):
    reports = db.execute(select(Report).where(Report.category == category)).scalars().all()
    if len(reports) < MIN_SAMPLES:
        return []

    coords = np.array([
        [radians(to_shape(r.geom).y), radians(to_shape(r.geom).x)] for r in reports
    ])
    labels = DBSCAN(eps=EPS_RAD, min_samples=MIN_SAMPLES, metric="haversine").fit(coords).labels_

    existing = db.execute(select(HazardCluster).where(HazardCluster.category == category)).scalars().all()
    touched_ids = []

    for label in set(labels):
        if label == -1:
            continue  # noise, not a cluster

        members = [r for r, l in zip(reports, labels) if l == label]
        lats = [to_shape(r.geom).y for r in members]
        lons = [to_shape(r.geom).x for r in members]
        centroid_lat, centroid_lon = sum(lats) / len(lats), sum(lons) / len(lons)
        centroid = from_shape(Point(centroid_lon, centroid_lat), srid=4326)

        matched = next(
            (c for c in existing if haversine_m(to_shape(c.geom).y, to_shape(c.geom).x, centroid_lat, centroid_lon) <= EPS_METERS),
            None,
        )

        if matched:
            matched.geom = centroid
            matched.report_count = len(members)
            cluster = matched
        else:
            cluster = HazardCluster(
                category=category, geom=centroid,
                status=ClusterStatus.forming, confidence=0, report_count=len(members),
            )
            db.add(cluster)
            db.flush()  # need cluster.id before assigning to reports

        for r in members:
            r.cluster_id = cluster.id
        touched_ids.append(cluster.id)

    db.commit()
    return touched_ids