from datetime import datetime
from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    subject_id: str
    title: str = Field(min_length=1, max_length=200)
    deadline: datetime
    required_hours: float = Field(gt=0, le=100)
    priority: int = Field(ge=1, le=5)


class AssignmentUpdate(BaseModel):
    """Partial update."""
    subject_id: str | None = None
    title: str | None = Field(None, min_length=1, max_length=200)
    deadline: datetime | None = None
    required_hours: float | None = Field(None, gt=0, le=100)
    priority: int | None = Field(None, ge=1, le=5)


class AssignmentResponse(BaseModel):
    assignment_id: str
    subject_id: str
    subject_name: str
    title: str
    deadline: datetime
    required_hours: float
    priority: int
    days_until_deadline: int
    is_overdue: bool


class AssignmentListResponse(BaseModel):
    assignments: list[AssignmentResponse]


class AssignmentStatsResponse(BaseModel):
    total: int
    overdue: int
    due_soon: int  # <= 3 days
    high_priority: int  # priority >= 4
    total_required_hours: float
