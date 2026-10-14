"""Tier 1 endpoint — proxies to Tier 2 risk-indicator service."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.orm_models import User
from app.services.risk_service import fetch_risk_score

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/score")
async def get_risk_score(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get workload risk score for current user.

    Aggregates behavioral data from DB, then calls Tier 2 service.
    """
    return await fetch_risk_score(str(user.user_id), db)
