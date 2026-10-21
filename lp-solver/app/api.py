"""FastAPI router for LP Solver."""
from fastapi import APIRouter

from .schemas import (
    ScheduleRequest, ScheduleResponse,
    InfeasibleResponse, Warning, ScheduleEntry,
    ConstraintExplanation, SubjectExplanation, DayExplanation,
    Conflict,
)
from .solver import solve_schedule

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("/generate", response_model=None)
def generate_schedule(req: ScheduleRequest) -> dict:
    """
    Generate an optimized study schedule.

    Uses MILP with diminishing returns (piecewise-linear approximation of √x).
    Risk score should already be applied to max_daily_hours (W_max_effective)
    by the caller (Tier 1).
    """
    input_data = req.model_dump()
    result = solve_schedule(input_data)
    return result
