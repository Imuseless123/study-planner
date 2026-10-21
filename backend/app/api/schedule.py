"""Schedule endpoints — proxy to Tier 3 via Tier 1 aggregation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.orm_models import User
from app.services.schedule_service import (
    generate_schedule_for_user,
    get_latest_schedule,
)

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("/generate")
async def generate(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an optimized study schedule from user's assignments.

    Pipeline:
    1. Aggregate assignments → LP subjects
    2. Get risk score from Tier 2
    3. Compute W_max_effective = W_max × (1 − α·risk)
    4. Call Tier 3 MILP solver
    5. Fallback to W_max if infeasible
    6. Persist to DB
    """
    return await generate_schedule_for_user(str(user.user_id), db)


@router.get("/latest")
def latest(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the most recent schedule for current user."""
    result = get_latest_schedule(str(user.user_id), db)
    if result is None:
        raise HTTPException(404, "No schedule generated yet")
    return result
