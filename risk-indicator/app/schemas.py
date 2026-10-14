"""Pydantic schemas for Risk Indicator API."""
from pydantic import BaseModel, Field


class RiskRequest(BaseModel):
    """Input for risk score calculation."""
    sleep_hours: float = Field(
        ge=0, le=24,
        description="Average sleep hours per day over past week",
        examples=[7.5],
    )
    required_hours: float = Field(
        ge=0, le=100,               # ← CHANGED: gt=0 → ge=0
        description="Total hours needed to complete upcoming work "
                    "(0 if no upcoming assignments)",
        examples=[15.0],
    )
    available_hours: float = Field(
        gt=0, le=200,
        description="Total hours available before deadline",
        examples=[40.0],
    )
    days_until_deadline: int = Field(
        ge=0, le=365,
        description="Days remaining to nearest deadline",
        examples=[5],
    )
    study_std: float = Field(
        ge=0, le=20,
        description="Std deviation of daily study hours over past 7 days",
        examples=[1.2],
    )


class RiskComponents(BaseModel):
    """Normalized component values (each in [0, 1])."""
    sleep_deficit: float
    workload_density: float
    deadline_proximity: float
    study_inconsistency: float


class RiskWeights(BaseModel):
    """Weights used in the risk formula."""
    sleep_deficit: float
    workload_density: float
    deadline_proximity: float
    study_inconsistency: float


class RiskResponse(BaseModel):
    """Response with risk score, level, components, and disclaimer."""
    risk_score: float = Field(ge=0, le=100)
    level: str
    components: RiskComponents
    weights: RiskWeights
    disclaimer: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
