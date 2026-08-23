from database import SessionLocal
from clustering import cluster_database_reports


db = SessionLocal()

try:
    clusters = cluster_database_reports(
        db,
        eps_meters=500,
        min_samples=2
    )

    print("Database clusters:")

    for i, cluster in enumerate(clusters):
        print(f"Cluster {i + 1}:")
        print([report["id"] for report in cluster])

finally:
    db.close()