from database import SessionLocal
from models import HazardCluster
from consensus import update_cluster_confidence


db = SessionLocal()

try:
    cluster = db.query(HazardCluster).first()

    if not cluster:
        print("No cluster found.")
    else:
        print("Before:")
        print("Status:", cluster.status)
        print("Confidence:", cluster.confidence)

        updated_cluster = update_cluster_confidence(
            db,
            cluster.id
        )

        print("\nAfter:")
        print("Status:", updated_cluster.status)
        print("Confidence:", updated_cluster.confidence)

finally:
    db.close()