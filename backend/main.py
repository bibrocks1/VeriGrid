import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from adapters.routing_adapter import RoutingAPIError
from clustering import recompute_clusters_for_category
from database import get_db
from mireye_service import CATEGORY_PRESET, fetch_area_context, score_report_credibility
from models import (
    AuthorityComplaint,
    ClusterStatus,
    ComplaintStatus,
    HazardCluster,
    MireyeSyncLog,
    Report,
    User,
)
from notifications.nearby_alerts import get_nearby_verified_clusters
from reasoning.agent import ReasoningAgentError, assess_hazard
from reasoning.assess_cluster import ClusterNotFoundError, assess_cluster
from reasoning.authority_agent import AuthorityAgentError, deliver_complaint
from reasoning.generate_complaint_for_cluster import generate_complaint_for_cluster
from reasoning.retrieval import retrieve_context
from routing.safe_route import get_safe_route
from schemas import ChatRequest, ComplaintOut, ReportCreate

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
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Day 9's RAG pipeline: retrieve VeriGrid + MirEye + NOAA evidence,
    then ask the reasoning agent to assess it. The request/response shape
    here matches what ChatPanel.jsx actually sends and renders
    ({message, location, context} -> {role, source, text}) — an earlier
    version of this route used {lat, lon, question} -> {answer}, which
    didn't match the frontend at all."""
    try:
        context = retrieve_context(
            db=db,
            lat=request.location.lat,
            lon=request.location.lng,
            radius_m=5000,
        )
        result = assess_hazard(question=request.message, context=context)
    except ReasoningAgentError as exc:
        raise HTTPException(status_code=502, detail=f"Unable to process hazard query: {exc}")

    text = (
        f"Severity: {result['severity']}\n\n"
        f"{result['explanation']}\n\n"
        f"Recommended action: {result['recommended_action']}"
    )

    # Attribute the answer to whichever source actually carried the key
    # fact: if VeriGrid had no reports/clusters nearby, the answer had to
    # come from MirEye/NOAA context instead.
    has_verigrid_evidence = bool(
        context["verigrid"]["reports"] or context["verigrid"]["verified_clusters"]
    )
    source = "verigrid" if has_verigrid_evidence else "mireye"

    return {"role": "assistant", "source": source, "text": text}


def _report_to_dict(report: Report) -> dict:
    point = to_shape(report.geom)
    return {
        "id": str(report.id),
        "category": report.category.value,
        "description": report.description,
        "lat": point.y,
        "lng": point.x,
        "createdAt": report.created_at.isoformat() if report.created_at else None,
        "reporterTrust": report.user.trust_score,
        "mireyeCredibility": (
            {"score": report.mireye_credibility_score, "notes": report.mireye_credibility_notes}
            if report.mireye_credibility_score is not None
            else None
        ),
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
        "severity": cluster.severity,
        "explanation": cluster.explanation,
        "recommendedAction": cluster.recommended_action,
    }


@app.post("/reports")
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    """Day 4: restored — this route didn't exist at all on main, so
    citizens couldn't submit a report. Anonymous identity via device_id
    (frontend/src/lib/deviceId.js), find-or-create a User row for it."""
    user = db.query(User).filter(User.device_id == payload.device_id).first()
    if user is None:
        user = User(device_id=payload.device_id, trust_score=10.0)
        db.add(user)
        db.flush()  # assign an id before the report references it

    report = Report(
        user_id=user.id,
        category=payload.category,
        description=payload.description,
        geom=from_shape(Point(payload.lng, payload.lat), srid=4326),
    )

    # Day 2's "check feasibility if the report is credible" idea: fetch
    # MirEye's terrain/hazard context for this coordinate and score how
    # consistent it is with the reported category. Advisory only — a MirEye
    # outage or an unmapped category never blocks report creation.
    preset = CATEGORY_PRESET.get(payload.category)
    if preset is not None:
        context = fetch_area_context(db, payload.lat, payload.lng, preset, kind="report_credibility")
        score, notes = score_report_credibility(payload.category, context)
        report.mireye_credibility_score = score
        report.mireye_credibility_notes = notes

    db.add(report)
    db.commit()
    db.refresh(report)

    # Recomputes confidence for every touched cluster internally, and
    # prunes clusters left with no members — matching the doc's "trigger
    # this inline after report submission" option.
    recompute_clusters_for_category(db, payload.category)
    db.refresh(report)

    return _report_to_dict(report)


@app.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    return [_report_to_dict(r) for r in reports]


@app.get("/reports/nearby")
def list_nearby_reports(
    lat: float,
    lng: float,
    radius_m: float = 5000,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    """Day 5: reports within `radius_m` meters of (lat, lng), optionally
    filtered by category. Report.geom is Geography, so ST_DWithin/
    ST_Distance operate in real meters, not degrees."""
    origin = from_shape(Point(lng, lat), srid=4326)
    distance = func.ST_Distance(Report.geom, origin).label("distance_m")
    query = db.query(Report, distance).filter(func.ST_DWithin(Report.geom, origin, radius_m)).order_by(distance)
    if category is not None:
        query = query.filter(Report.category == category)

    return [{**_report_to_dict(report), "distanceM": round(distance_m, 1)} for report, distance_m in query.all()]


@app.get("/clusters")
def list_clusters(db: Session = Depends(get_db)):
    clusters = db.query(HazardCluster).filter(HazardCluster.status != ClusterStatus.forming).all()
    return [_cluster_to_dict(c, db) for c in clusters]


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    active_reports = db.query(func.count(Report.id)).scalar()
    verified_hotspots = (
        db.query(func.count(HazardCluster.id)).filter(HazardCluster.status == ClusterStatus.verified).scalar()
    )
    trust_contributors = db.query(func.count(func.distinct(Report.user_id))).scalar()

    return {
        "activeReports": active_reports or 0,
        "verifiedHotspots": verified_hotspots or 0,
        "trustContributors": trust_contributors or 0,
    }


@app.post("/clusters/{cluster_id}/assess")
def assess_cluster_endpoint(cluster_id: int, db: Session = Depends(get_db)):
    """Day 9/10: runs the reasoning agent against this cluster's location
    and persists severity/explanation/recommended_action onto it, so the
    map and an authority complaint always agree on severity."""
    try:
        cluster = assess_cluster(db, cluster_id)
    except ClusterNotFoundError:
        raise HTTPException(status_code=404, detail=f"No cluster with id={cluster_id}")
    except ReasoningAgentError as exc:
        raise HTTPException(status_code=502, detail=f"Reasoning agent failed: {exc}")

    return _cluster_to_dict(cluster, db)


def _complaint_to_dict(complaint: AuthorityComplaint) -> dict:
    return {
        "clusterId": complaint.cluster_id,
        "issueType": complaint.title,
        "location": complaint.location,
        "severity": complaint.severity,
        "confidence": complaint.confidence,
        "contributorCount": complaint.contributor_count,
        "identifiedAuthority": complaint.responsible_authority,
        "status": complaint.status.value,
        "draftText": complaint.description,
    }


@app.get("/clusters/{cluster_id}/report")
def get_cluster_authority_report(cluster_id: int, db: Session = Depends(get_db)):
    """Day 11: matches what AuthorityReportCard.jsx / ReportReviewScreen.jsx
    actually call. Only verified clusters get a report — candidate/forming
    clusters haven't cleared consensus yet."""
    cluster = db.query(HazardCluster).filter(HazardCluster.id == cluster_id).first()
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if cluster.status != ClusterStatus.verified:
        raise HTTPException(status_code=400, detail="Cluster is not verified yet")

    try:
        complaint = generate_complaint_for_cluster(db, cluster_id)
    except ClusterNotFoundError:
        raise HTTPException(status_code=404, detail=f"No cluster with id={cluster_id}")
    except (ReasoningAgentError, AuthorityAgentError) as exc:
        raise HTTPException(status_code=502, detail=f"Complaint generation failed: {exc}")

    return _complaint_to_dict(complaint)


@app.post("/clusters/{cluster_id}/send-report")
def send_cluster_authority_report(cluster_id: int, db: Session = Depends(get_db)):
    """Day 12: the human-approval step happens on the frontend (draft ->
    approved is local state in ReportReviewScreen.jsx); this is the single
    backend action triggered once a reviewer clicks "Approve and send" —
    it marks the complaint sent and attempts delivery. This route didn't
    exist anywhere on main."""
    complaint = db.query(AuthorityComplaint).filter(AuthorityComplaint.cluster_id == cluster_id).first()
    if complaint is None:
        raise HTTPException(status_code=404, detail="No draft report exists for this cluster yet")
    if complaint.status == ComplaintStatus.sent:
        return _complaint_to_dict(complaint)

    complaint.delivery_detail = deliver_complaint(complaint)
    complaint.status = ComplaintStatus.sent
    complaint.sent_at = func.now()
    db.commit()
    db.refresh(complaint)
    return _complaint_to_dict(complaint)


@app.post("/clusters/{cluster_id}/generate-complaint", response_model=ComplaintOut)
def generate_complaint_endpoint(cluster_id: int, db: Session = Depends(get_db)):
    """Same underlying generator as GET /clusters/{id}/report, exposed
    with main's original snake_case contract too for API completeness."""
    try:
        complaint = generate_complaint_for_cluster(db, cluster_id)
    except ClusterNotFoundError:
        raise HTTPException(status_code=404, detail=f"No cluster with id={cluster_id}")
    except (ReasoningAgentError, AuthorityAgentError) as exc:
        raise HTTPException(status_code=502, detail=f"Complaint generation failed: {exc}")

    return complaint


@app.get("/complaints", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    """Lists all authority complaints (draft/approved/sent)."""
    return db.execute(select(AuthorityComplaint).order_by(AuthorityComplaint.created_at.desc())).scalars().all()


@app.get("/alerts/nearby")
def get_nearby_alerts(lat: float, lon: float, radius: float = 3000, db: Session = Depends(get_db)):
    """Polling endpoint: the frontend can call this on an interval while
    the map is open and diff client-side against what it last saw. Only
    returns VERIFIED clusters."""
    return {"alerts": get_nearby_verified_clusters(db, lat, lon, radius)}


@app.get("/route/safe")
def get_safe_route_endpoint(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    db: Session = Depends(get_db),
):
    """Day 10: OSRM -> route geometry -> VeriGrid checks geometry against
    hazards -> safe route response. Selects among a few alternative
    routes and picks the first that clears all verified-hazard buffers;
    if none do, returns the shortest with an explicit warning."""
    try:
        return get_safe_route(db, origin_lat, origin_lng, dest_lat, dest_lng)
    except RoutingAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Routing service failed: {exc}")


@app.get("/clusters/{cluster_id}/mireye-payload")
def get_cluster_mireye_payload(cluster_id: int, db: Session = Depends(get_db)):
    """Day 8: the full observation payload VeriGrid built and would push to
    MirEye the moment this cluster verified. MirEye's API has no write
    endpoint (see adapters/mireye_adapter.push_verified_observation), so
    this was never sent over the network, but every field is real and
    already computed, ready to send the instant a write endpoint exists."""
    log = (
        db.query(MireyeSyncLog)
        .filter(MireyeSyncLog.cluster_id == cluster_id, MireyeSyncLog.kind == "verified_push")
        .order_by(MireyeSyncLog.created_at.desc())
        .first()
    )
    if log is None:
        raise HTTPException(
            status_code=404, detail="No prepared MirEye payload for this cluster (it may not be verified yet)"
        )
    return {
        "clusterId": cluster_id,
        "status": "prepared_not_sent",
        "preparedAt": log.created_at.isoformat() if log.created_at else None,
        "payload": json.loads(log.detail),
    }


@app.get("/mireye/sync-log")
def get_mireye_sync_log(db: Session = Depends(get_db)):
    """Matches SyncStatusBadge.jsx's {lastSyncedAt, status, recordsSynced}
    shape. MirEye's API has no write endpoint, so "synced" here means real
    MirEye reads logged — report-credibility checks and chat-context
    lookups — not pushed observations."""
    latest = db.query(MireyeSyncLog).order_by(MireyeSyncLog.created_at.desc()).first()
    records_synced = db.query(func.count(MireyeSyncLog.id)).filter(MireyeSyncLog.status == "ok").scalar() or 0
    if latest is None:
        return {"lastSyncedAt": None, "status": "failed", "recordsSynced": 0}
    return {
        "lastSyncedAt": latest.created_at.isoformat() if latest.created_at else None,
        "status": latest.status,
        "recordsSynced": records_synced,
    }
