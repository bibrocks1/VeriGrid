from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from models import ReportCategory, ClusterStatus, ComplaintStatus


class ReportCreate(BaseModel):
    # device_id, not user_id: the frontend has no login system — an
    # anonymous browser is identified by a localStorage-generated UUID
    # (frontend/src/lib/deviceId.js) and POST /reports finds-or-creates the
    # matching User row. lng (not lon) matches ReportForm.jsx's actual
    # payload field name.
    category: ReportCategory
    description: Optional[str] = None
    lat: float
    lng: float
    device_id: str = Field(min_length=1)

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError(f"Invalid latitude: {v}")
        return v

    @field_validator("lng")
    @classmethod
    def validate_lng(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError(f"Invalid longitude: {v}")
        return v


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
    severity: Optional[str] = None
    explanation: Optional[str] = None
    recommended_action: Optional[str] = None
    assessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatLocation(BaseModel):
    lat: float
    lng: float


class ChatMessage(BaseModel):
    role: str
    source: Optional[str] = None
    text: str


# Matches what ChatPanel.jsx actually sends via lib/api.js's
# sendChatMessage: { message, location, context }. Reconciled from main's
# {lat, lon, question} -> {answer} contract, which didn't match what the
# frontend chat panel sends or renders.
class ChatRequest(BaseModel):
    message: str
    location: ChatLocation
    context: list[ChatMessage] = []


class ComplaintOut(BaseModel):
    id: int
    cluster_id: int
    title: str
    description: str
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    responsible_authority: str
    location: Optional[str] = None
    confidence: Optional[int] = None
    contributor_count: Optional[int] = None
    status: ComplaintStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True
