from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models import ReportCategory, ClusterStatus


class ReportCreate(BaseModel):
    user_id: UUID
    category: ReportCategory
    description: Optional[str] = None
    lat: float
    lon: float


class ReportOut(BaseModel):
    id: UUID
    user_id: UUID
    category: ReportCategory
    description: Optional[str] = None
    lat: float
    lon: float
    cluster_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClusterOut(BaseModel):
    id: int
    category: ReportCategory
    status: ClusterStatus
    confidence: int
    report_count: int
    lat: float
    lon: float

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    lat: float
    lon: float
    question: str


class ChatResponse(BaseModel):
    answer: str