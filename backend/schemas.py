from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models import ReportCategory, ClusterStatus
# What does the API key return/accept

class ReportCreate(BaseModel):
    user_id: int
    category: ReportCategory
    description: Optional[str] = None
    lat: float
    lon: float


class ReportOut(BaseModel):
    id: int
    user_id: int
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

class ClusterOut(BaseModel):
    id: int
    category: str
    status: str
    confidence: int
    report_count: int
    lat: float
    lon: float

    class Config:
        from_attributes = True