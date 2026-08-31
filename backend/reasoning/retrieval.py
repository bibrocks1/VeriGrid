from sqlalchemy import select, func
from sqlalchemy.orm import Session

from geoalchemy2.shape import to_shape

from models import Report, HazardCluster, ClusterStatus
from adapters.mireye_adapter import get_area_context
from adapters.noaa_adapter import get_weather_context


def retrieve_context(
    db: Session,
    lat: float,
    lon: float,
    radius_m: float = 5000,
):
    """
    Retrieve structured evidence around a location.

    Sources remain separate:
    - VeriGrid: citizen reports and verified clusters
    - MirEye: geospatial/infrastructure context
    - NOAA: weather context
    """

    # ---------------------------------------------------------
    # 1. Build the query point
    # ---------------------------------------------------------

    point = func.ST_SetSRID(
        func.ST_MakePoint(lon, lat),
        4326,
    )

    # ---------------------------------------------------------
    # 2. Retrieve nearby reports
    # ---------------------------------------------------------

    reports = (
        db.execute(
            select(Report)
            .where(
                func.ST_DWithin(
                    Report.geom,
                    point,
                    radius_m,
                )
            )
            .order_by(Report.created_at.desc())
        )
        .scalars()
        .all()
    )

    verigrid_reports = []

    for report in reports:
        shape = to_shape(report.geom)

        verigrid_reports.append(
            {
                "id": str(report.id),
                "user_id": str(report.user_id),
                "category": (
                    report.category.value
                    if hasattr(report.category, "value")
                    else str(report.category)
                ),
                "description": report.description,
                "lat": shape.y,
                "lon": shape.x,
                "cluster_id": report.cluster_id,
                "created_at": (
                    report.created_at.isoformat()
                    if report.created_at
                    else None
                ),
            }
        )

    # ---------------------------------------------------------
    # 3. Retrieve nearby verified clusters
    # ---------------------------------------------------------

    clusters = (
        db.execute(
            select(HazardCluster)
            .where(
                HazardCluster.status
                == ClusterStatus.verified
            )
            .where(
                func.ST_DWithin(
                    HazardCluster.geom,
                    point,
                    radius_m,
                )
            )
            .order_by(
                HazardCluster.confidence.desc()
            )
        )
        .scalars()
        .all()
    )

    verigrid_clusters = []

    for cluster in clusters:
        shape = to_shape(cluster.geom)

        verigrid_clusters.append(
            {
                "id": cluster.id,
                "category": (
                    cluster.category.value
                    if hasattr(cluster.category, "value")
                    else str(cluster.category)
                ),
                "status": (
                    cluster.status.value
                    if hasattr(cluster.status, "value")
                    else str(cluster.status)
                ),
                "confidence": cluster.confidence,
                "report_count": cluster.report_count,
                "severity": cluster.severity,
                "explanation": cluster.explanation,
                "recommended_action": cluster.recommended_action,
                "lat": shape.y,
                "lon": shape.x,
                "created_at": (
                    cluster.created_at.isoformat()
                    if cluster.created_at
                    else None
                ),
            }
        )

    # ---------------------------------------------------------
    # 4. MirEye context
    # ---------------------------------------------------------

    mireye = None
    mireye_error = None

    try:
        mireye = get_area_context(
            lat,
            lon,
        )
    except Exception as exc:
        mireye_error = str(exc)

    # ---------------------------------------------------------
    # 5. NOAA context
    # ---------------------------------------------------------

    noaa = None
    noaa_error = None

    try:
        noaa = get_weather_context(
            lat,
            lon,
        )
    except Exception as exc:
        noaa_error = str(exc)

    # ---------------------------------------------------------
    # 6. Keep sources completely separate
    # ---------------------------------------------------------

    return {
        "location": {
            "lat": lat,
            "lon": lon,
            "radius_m": radius_m,
        },

        "verigrid": {
            "reports": verigrid_reports,
            "verified_clusters": verigrid_clusters,
        },

        "mireye": mireye,

        "mireye_error": mireye_error,

        "noaa": noaa,

        "noaa_error": noaa_error,
    }