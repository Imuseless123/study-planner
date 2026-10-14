"""FastAPI router for Risk Indicator."""
from fastapi import APIRouter, HTTPException, status

from .calculator import (
    DISCLAIMER,
    compute_risk,
    RiskResult,
)
from .schemas import (
    RiskRequest,
    RiskResponse,
    RiskComponents,
    RiskWeights,
)

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.post("/score", response_model=RiskResponse)
def compute_risk_score(req: RiskRequest) -> RiskResponse:
    """
    Compute workload risk score from behavioral inputs.

    This endpoint uses rule-based scoring (no ML) to ensure:
    - Transparency (formula is public, auditable)
    - Reproducibility (same input → same output)
    - Ethical safety (no medical/psychological diagnosis)

    The response ALWAYS includes a disclaimer.
    """
    try:
        result: RiskResult = compute_risk(
            sleep_hours=req.sleep_hours,
            required_hours=req.required_hours,
            available_hours=req.available_hours,
            days_until_deadline=req.days_until_deadline,
            study_std=req.study_std,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    return RiskResponse(
        risk_score=result.risk_score,
        level=result.level,
        components=RiskComponents(**result.components),
        weights=RiskWeights(**result.weights),
        disclaimer=DISCLAIMER,
    )
