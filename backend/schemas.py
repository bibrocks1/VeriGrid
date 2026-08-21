from pydantic import BaseModel, Field, field_validator

from models import ReportCategory


class ReportCreate(BaseModel):
    category: ReportCategory
    description: str | None = None
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


# Not wired up yet — Day 9's RAG chat endpoint isn't implemented. Kept here
# as the agreed request/response contract so that work has a starting point.
class ChatRequest(BaseModel):
    lat: float
    lon: float
    question: str


class ChatResponse(BaseModel):
    answer: str
