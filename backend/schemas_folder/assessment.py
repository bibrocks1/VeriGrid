from typing import Literal

from pydantic import BaseModel, Field


class ClusterAssessment(BaseModel):
    severity: Literal["low", "moderate", "high", "critical"]
    explanation: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)