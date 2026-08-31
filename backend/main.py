from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point
from adapters.mireye_adapter import get_area_context
from consensus import update_cluster_confidence
from database import get_db
from schemas import ChatRequest, ChatResponse, ReportCreate, ReportOut
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import Float

from schemas import ReportOut

from models import ClusterStatus, Report, HazardCluster, User

from clustering import run_clustering_for_category


from schemas import (
    ChatRequest,
    ChatResponse,
    ReportCreate,
    ReportOut,
    ClusterOut,
    ComplaintOut,
)

from reasoning.retrieval import retrieve_context
from reasoning.agent import assess_hazard, ReasoningAgentError
from reasoning.assess_cluster import assess_cluster, ClusterNotFoundError
from reasoning.generate_complaint_for_cluster import generate_complaint_for_cluster
from reasoning.authority_agent import AuthorityAgentError
from notifications.nearby_alerts import get_nearby_verified_clusters
from adapters.routing_adapter import RoutingAPIError
from routing.safe_route import get_safe_route
from models import AuthorityComplaint, ComplaintStatus


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
    return {
        "status": "ok",
        "message": "Backend is running!"
    }

@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Location-aware hazard reasoning endpoint.

    Flow:
        user question
            ↓
        retrieve VeriGrid + MirEye + NOAA
            ↓
        OpenAI reasoning agent
            ↓
        grounded answer
    """

    try:
        # 1. Retrieve evidence around the requested location
        context = retrieve_context(
            db=db,
            lat=request.lat,
            lon=request.lon,
            radius_m=5000,
        )

        # 2. Ask the reasoning agent to assess the evidence
        result = assess_hazard(
            question=request.question,
            context=context,
        )

        # 3. Convert structured reasoning into a user-facing answer
        answer = (
            f"Severity: {result['severity']}\n\n"
            f"Explanation: {result['explanation']}\n\n"
            f"Recommended Action: {result['recommended_action']}\n\n"
            f"Evidence:\n"
            f"- VeriGrid: {result['evidence_summary']['verigrid']}\n"
            f"- MirEye: {result['evidence_summary']['mireye']}\n"
            f"- NOAA: {result['evidence_summary']['noaa']}"
        )

        return ChatResponse(answer=answer)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process hazard query: {exc}",
        )

@app.post("/reports", response_model=ReportOut)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    """
    Creates a new citizen hazard report and triggers cluster
    recomputation for that category inline — simplest correct choice at
    this scale, no background job queue needed for a hackathon demo.

    Unlike an earlier draft of this endpoint (which auto-registered an
    anonymous User from a device_id), the current User model has no
    device_id column — it's just id (UUID) / trust_score / created_at.
    So payload.user_id must reference an EXISTING User row; if it
    doesn't, this returns 404 rather than letting a dangling foreign key
    hit the database as a raw IntegrityError.
    """
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"No user with id={payload.user_id}")

    report = Report(
        user_id=user.id,
        category=payload.category,
        description=payload.description,
        geom=from_shape(Point(payload.lon, payload.lat), srid=4326),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Recompute clusters for this category inline so the new report is
    # reflected in /clusters immediately, rather than waiting on a
    # separate background job.
    run_clustering_for_category(db, payload.category)
    db.refresh(report)

    shape = to_shape(report.geom)
    return {
        "id": report.id,
        "user_id": report.user_id,
        "category": report.category,
        "description": report.description,
        "lat": shape.y,
        "lon": shape.x,
        "cluster_id": report.cluster_id,
        "created_at": report.created_at,
    }


@app.get("/reports", response_model=list[ReportOut])
def get_reports(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            Report.id,
            Report.user_id,
            Report.category,
            Report.description,
            func.ST_Y(Report.geom.cast(Geometry)).label("lat"),
            func.ST_X(Report.geom.cast(Geometry)).label("lon"),
            Report.cluster_id,
            Report.created_at,
        )
    ).all()

    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "category": row.category,
            "description": row.description,
            "lat": row.lat,
            "lon": row.lon,
            "cluster_id": row.cluster_id,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@app.get("/reports/nearby", response_model=list[ReportOut])
def get_nearby_reports(
    lat: float,
    lon: float,
    radius: float = 5000,
    db: Session = Depends(get_db)
):
    point = func.ST_SetSRID(
        func.ST_MakePoint(lon, lat),
        4326
    )

    rows = db.execute(
        select(
            Report.id,
            Report.user_id,
            Report.category,
            Report.description,
            func.ST_Y(
                Report.geom.cast(Geometry)
            ).label("lat"),
            func.ST_X(
                Report.geom.cast(Geometry)
            ).label("lon"),
            Report.cluster_id,
            Report.created_at,
        )
        .where(
            func.ST_DWithin(
                Report.geom,
                point,
                radius
            )
        )
    ).all()

    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "category": row.category,
            "description": row.description,
            "lat": row.lat,
            "lon": row.lon,
            "cluster_id": row.cluster_id,
            "created_at": row.created_at,
        }
        for row in rows
    ]



from geoalchemy2 import Geometry
from sqlalchemy import func

@app.get("/clusters", response_model=list[ClusterOut])
def get_clusters(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            HazardCluster.id, HazardCluster.category, HazardCluster.status,
            HazardCluster.confidence, HazardCluster.report_count,
            func.ST_Y(HazardCluster.geom.cast(Geometry)).label("lat"),
            func.ST_X(HazardCluster.geom.cast(Geometry)).label("lon"),
            HazardCluster.severity, HazardCluster.explanation,
            HazardCluster.recommended_action, HazardCluster.assessed_at,
        )
    ).all()
    return [
        {
            "id": row.id,
            "category": row.category,
            "status": row.status,
            "confidence": row.confidence,
            "report_count": row.report_count,
            "lat": row.lat,
            "lon": row.lon,
            "severity": row.severity,
            "explanation": row.explanation,
            "recommended_action": row.recommended_action,
            "assessed_at": row.assessed_at,
        }
        for row in rows
    ]


@app.post("/clusters/{cluster_id}/assess", response_model=ClusterOut)
def assess_cluster_endpoint(cluster_id: int, db: Session = Depends(get_db)):
    """
    Runs the Day 9 reasoning agent against this specific cluster's
    location and persists severity/explanation/recommended_action onto
    it. Idempotent-ish: re-running overwrites the previous assessment
    with a fresh one (no history is kept — a single current assessment
    per cluster is enough for the demo; see Day 12 backtesting for
    before/after comparisons instead).
    """
    try:
        cluster = assess_cluster(db, cluster_id)
    except ClusterNotFoundError:
        raise HTTPException(status_code=404, detail=f"No cluster with id={cluster_id}")
    except ReasoningAgentError as exc:
        raise HTTPException(status_code=502, detail=f"Reasoning agent failed: {exc}")

    shape = to_shape(cluster.geom)

    return {
        "id": cluster.id,
        "category": cluster.category,
        "status": cluster.status,
        "confidence": cluster.confidence,
        "report_count": cluster.report_count,
        "lat": shape.y,
        "lon": shape.x,
        "severity": cluster.severity,
        "explanation": cluster.explanation,
        "recommended_action": cluster.recommended_action,
        "assessed_at": cluster.assessed_at,
    }


# ---------------------------------------------------------------------
# OPTIONAL (Day 10) — nearby alerts + safe routing. Flagged cuttable in
# the Day 10 plan; cut these first if time is short, the map + chat +
# report flow demos fine without them.
# ---------------------------------------------------------------------

@app.get("/alerts/nearby")
def get_nearby_alerts(
    lat: float,
    lon: float,
    radius: float = 3000,
    db: Session = Depends(get_db),
):
    """
    Polling endpoint: the frontend calls this on an interval while the
    map is open and diffs client-side against what it last saw, rather
    than the backend pushing over a WebSocket. Only returns VERIFIED
    clusters — candidate/forming clusters aren't confirmed hazards yet.
    """
    return {"alerts": get_nearby_verified_clusters(db, lat, lon, radius)}


@app.get("/route/safe")
def get_safe_route_endpoint(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    db: Session = Depends(get_db),
):
    """
    Returns a route that avoids verified-hazard buffers where possible.
    NOT true avoid-polygon routing — selects among a few alternative
    routes from the routing engine and picks the first one whose path
    doesn't pass within HAZARD_BUFFER_METERS of a verified cluster. If
    none qualify, returns the shortest option with an explicit warning
    rather than silently implying it's hazard-free.
    """
    try:
        return get_safe_route(db, origin_lat, origin_lon, dest_lat, dest_lon)
    except RoutingAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Routing service failed: {exc}")


# ---------------------------------------------------------------------
# Day 11 — Authority Agent
# ---------------------------------------------------------------------

@app.post("/clusters/{cluster_id}/generate-complaint", response_model=ComplaintOut)
def generate_complaint_endpoint(cluster_id: int, db: Session = Depends(get_db)):
    """
    Generates an evidence-backed authority complaint for a cluster and
    saves it as a draft. If the cluster hasn't been assessed yet (Day
    10's /clusters/{id}/assess), this runs that assessment first
    automatically — see reasoning/generate_complaint_for_cluster.py.
    """
    try:
        complaint = generate_complaint_for_cluster(db, cluster_id)
    except ClusterNotFoundError:
        raise HTTPException(status_code=404, detail=f"No cluster with id={cluster_id}")
    except (ReasoningAgentError, AuthorityAgentError) as exc:
        raise HTTPException(status_code=502, detail=f"Complaint generation failed: {exc}")

    return complaint


@app.get("/complaints", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    """Lists all authority complaints (draft/approved/sent) for the
    approval-queue UI."""
    return db.execute(
        select(AuthorityComplaint).order_by(AuthorityComplaint.created_at.desc())
    ).scalars().all()


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard summary numbers for the frontend. Only touches fields
    that definitely exist on the current models."""
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