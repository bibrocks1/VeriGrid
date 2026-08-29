from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from geoalchemy2 import Geometry
from adapters.mireye_adapter import get_area_context
from consensus import update_cluster_confidence
from database import get_db
from schemas import ChatRequest, ChatResponse, ReportCreate, ReportOut
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import Float

from schemas import ReportOut

from models import ClusterStatus, Report, HazardCluster

from clustering import run_clustering_for_category


from schemas import (
    ChatRequest,
    ChatResponse,
    ReportCreate,
    ReportOut,
    ClusterOut
)

from reasoning.retrieval import retrieve_context
from reasoning.agent import assess_hazard


app = FastAPI(title="VeriGrid API")


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
        }
        for row in rows
    ]