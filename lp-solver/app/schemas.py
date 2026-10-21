"""Pydantic schemas for LP Solver API."""
from pydantic import BaseModel, Field


class SubjectInput(BaseModel):
    """Subject with deadline and required hours."""
    id: str = Field(min_length=1, max_length=100)
    required_hours: float = Field(gt=0, le=100)
    deadline_day: int = Field(ge=0, le=365, description="Days from today")
    difficulty: int = Field(ge=1, le=5)
    priority: int = Field(ge=1, le=5)
    urgency: float | None = Field(
        None, ge=0, le=2, description="Auto-computed if not provided"
    )


class TimeSlotInput(BaseModel):
    """Time slot with availability and time-of-day factor."""
    day: int = Field(ge=0, le=365)
    slot: int = Field(ge=0, le=10, description="0=morning, 1=afternoon, 2=evening")
    tod_factor: float = Field(gt=0, le=2.0)
    available_hours: float = Field(ge=0, le=24)


class ScheduleRequest(BaseModel):
    """Request to generate a schedule."""
    subjects: list[SubjectInput] = Field(min_length=1, max_length=20)
    time_slots: list[TimeSlotInput] = Field(min_length=1)
    max_daily_hours: float = Field(gt=0, le=24, description="W_max_effective")
    min_session_hours: float = Field(default=0.5, gt=0, le=4)
    buffer_ratio: float = Field(default=0.25, ge=0, le=1)
    big_m: float = Field(default=8.0, gt=0, le=100)
    lambda_deadline: float = Field(
        default=20.0,
        ge=0,
        description="Penalty for deadline shortfall",
    )
    lambda_daily: float = Field(
        default=100.0,
        ge=0,
        description=(
            "Penalty for daily overload. Must be > max marginal gain "
            "(E×slope ≈ 35) so soft constraint dominates and solver "
            "never overflows to gain effectiveness."
        ),
    )


class ScheduleEntry(BaseModel):
    """One assigned study session."""
    subject_id: str
    day: int
    slot: int
    hours: float


class SubjectExplanation(BaseModel):
    """Per-subject breakdown of the schedule."""
    subject_id: str
    required_hours: float
    scheduled_hours: float
    buffer_used: float
    deadline_shortfall: float


class DayExplanation(BaseModel):
    """Per-day breakdown."""
    day: int
    total_hours: float
    overload: float


class ConstraintExplanation(BaseModel):
    per_subject: list[SubjectExplanation]
    per_day: list[DayExplanation]


class Warning(BaseModel):
    """Warning about the schedule."""
    type: str
    message: str
    subject_id: str | None = None
    day: int | None = None
    shortfall_hours: float | None = None
    overload_hours: float | None = None


class ScheduleResponse(BaseModel):
    """Successful schedule response."""
    status: str
    feasible: bool
    schedule: list[ScheduleEntry]
    explanation: ConstraintExplanation
    warnings: list[Warning]
    objective_value: float


class Conflict(BaseModel):
    """Conflict description for infeasible problems."""
    type: str
    message: str
    subject_id: str | None = None
    day: int | None = None


class InfeasibleResponse(BaseModel):
    """Response when problem is infeasible."""
    status: str
    feasible: bool
    conflicts: list[Conflict]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
