from clustering import cluster_reports


reports = [
    {
        "id": 1,
        "lat": 28.6139,
        "lon": 77.2090
    },
    {
        "id": 2,
        "lat": 28.6142,
        "lon": 77.2093
    },
    {
        "id": 3,
        "lat": 28.6136,
        "lon": 77.2087
    },

    # Far away group
    {
        "id": 4,
        "lat": 28.6200,
        "lon": 77.2200
    },
    {
        "id": 5,
        "lat": 28.6203,
        "lon": 77.2204
    }
]


clusters = cluster_reports(
    reports,
    eps_meters=500,
    min_samples=2
)

print("Clusters:")

for i, cluster in enumerate(clusters):
    print(f"Cluster {i + 1}:")
    print([report["id"] for report in cluster])