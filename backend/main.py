from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from geoalchemy2 import Geometry
from database import get_db
from schemas import ChatRequest, ChatResponse, ReportCreate, ReportOut
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import Float

from schemas import ReportOut

from models import Report, HazardCluster

from clustering import run_clustering_for_category
from schemas import (
    ChatRequest,
    ChatResponse,
    ReportCreate,
    ReportOut,
    ClusterOut
)

app = FastAPI(title="VeriGrid API")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend is running!"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return ChatResponse(
        answer="Chat functionality coming soon."
    )


@app.post("/reports", response_model=ReportOut)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db)
):
    db_report = Report(
        user_id=report.user_id,
        category=report.category,
        description=report.description,
        geom=WKTElement(
            f"POINT({report.lon} {report.lat})",
            srid=4326
        )
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    run_clustering_for_category(
    db,
    db_report.category
    )

    return ReportOut(
        id=db_report.id,
        user_id=db_report.user_id,
        category=db_report.category,
        description=db_report.description,
        lat=report.lat,
        lon=report.lon,
        cluster_id=db_report.cluster_id,
        created_at=db_report.created_at
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