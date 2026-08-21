from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from clustering import recompute_clusters_for_category
from database import get_db
from models import ClusterStatus, HazardCluster, Report, User
from schemas import ReportCreate

app = FastAPI(title="VeriGrid API")

app.add_middleware(
    CORSMiddleware,
    # Local dev only — the frontend always runs on :3000 in this setup
    # (npm run dev or docker-compose). Widen this once there's a deployed
    # frontend origin to allow.
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running!"}


@app.post("/chat")
def chat():
    return {
        "message": "Chat endpoint is ready for implementation."
    }


def _report_to_dict(report: Report) -> dict:
    point = to_shape(report.geom)
    return {
        "id": report.id,
        "category": report.category.value,
        "description": report.description,
        "lat": point.y,
        "lng": point.x,
        "createdAt": report.created_at.isoformat() if report.created_at else None,
        "reporterTrust": report.user.trust_score,
    }


def _cluster_to_dict(cluster: HazardCluster, db: Session) -> dict:
    point = to_shape(cluster.geom)
    members = (
        db.query(Report)
        .filter(Report.cluster_id == cluster.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    distinct_reporters = len({r.user_id for r in members})
    first_reported_at = min((r.created_at for r in members), default=cluster.created_at)
    latest_description = members[0].description if members else None

    return {
        "id": cluster.id,
        "category": cluster.category.value,
        "status": cluster.status.value,
        "confidence": cluster.confidence,
        "description": latest_description,
        "lat": point.y,
        "lng": point.x,
        "reporterCount": cluster.report_count,
        "distinctReporters": distinct_reporters,
        "firstReportedAt": first_reported_at.isoformat() if first_reported_at else None,
        "verifiedAt": cluster.verified_at.isoformat() if cluster.verified_at else None,
    }


@app.post("/reports")
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_id == payload.device_id).first()
    if user is None:
        user = User(device_id=payload.device_id, trust_score=10)
        db.add(user)
        db.flush()  # assign an id before the report references it

    report = Report(
        user_id=user.id,
        category=payload.category,
        description=payload.description,
        geom=from_shape(Point(payload.lng, payload.lat), srid=4326),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Inline recompute, matching the doc's "trigger this inline after report
    # submission" option — simplest correct choice at this scale.
    recompute_clusters_for_category(db, payload.category)
    db.refresh(report)

    return _report_to_dict(report)


@app.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).options(joinedload(Report.user)).all()
    return [_report_to_dict(r) for r in reports]


@app.get("/clusters")
def list_clusters(db: Session = Depends(get_db)):
    clusters = (
        db.query(HazardCluster)
        .filter(HazardCluster.status != ClusterStatus.forming)
        .all()
    )
    return [_cluster_to_dict(c, db) for c in clusters]


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    active_reports = db.query(func.count(Report.id)).scalar()
    verified_hotspots = (
        db.query(func.count(HazardCluster.id))
        .filter(HazardCluster.status == ClusterStatus.verified)
        .scalar()
    )
    trust_contributors = db.query(func.count(func.distinct(Report.user_id))).scalar()

    return {
        "activeReports": active_reports or 0,
        "verifiedHotspots": verified_hotspots or 0,
        "trustContributors": trust_contributors or 0,
    }
