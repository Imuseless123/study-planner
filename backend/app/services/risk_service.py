"""Service to fetch risk score from Tier 2 (Risk Indicator)."""
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.repositories.log_repo import LogRepository
from app.repositories.assignment_repo import AssignmentRepository

settings = get_settings()


async def fetch_risk_score(user_id: str, db) -> dict:
    """
    Aggregate behavioral data + workload, then call Tier 2 for risk score.

    Returns the full Tier 2 response: {risk_score, level, components, weights, disclaimer}.
    """
    log_repo = LogRepository(db)
    assignment_repo = AssignmentRepository(db)

    # 1. Sleep hours (avg 7 ngày)
    sleep_list = log_repo.get_sleep_hours_last_n_days(user_id, n=7)
    avg_sleep = sum(sleep_list) / len(sleep_list) if sleep_list else 7.0

    # 2. Study std (population std — khớp thesis §3.6.2)
    study_by_date = log_repo.get_study_hours_last_n_days(user_id, n=7)
    study_vals = list(study_by_date.values())
    if len(study_vals) >= 2:
        mean = sum(study_vals) / len(study_vals)
        variance = sum((v - mean) ** 2 for v in study_vals) / len(study_vals)
        study_std = variance ** 0.5
    else:
        study_std = 0.0

    # 3. Workload từ assignments
    upcoming = assignment_repo.list_upcoming(user_id, days=30)
    if not upcoming:
        required_hours = 0.0
        days_until = 30
    else:
        required_hours = sum(float(a.required_hours) for a in upcoming)
        nearest = min(upcoming, key=lambda a: a.deadline)
        now = datetime.now(timezone.utc)
        deadline = nearest.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        days_until = max(0, (deadline - now).days)

    available_hours = max(1.0, days_until * 6.0)

    payload = {
        "sleep_hours": round(avg_sleep, 2),
        "required_hours": round(required_hours, 2),
        "available_hours": round(available_hours, 2),
        "days_until_deadline": days_until,
        "study_std": round(study_std, 2),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            r = await http.post(
                f"{settings.RISK_API_URL}/api/risk/score", json=payload,
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Risk Indicator service unavailable: {e}",
        ) from e
