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
    Compute risk score by:
    1. Aggregating behavioral data from DB (sleep, study)
    2. Computing workload stats from assignments
    3. Calling Tier 2 service
    """
    log_repo = LogRepository(db)
    assignment_repo = AssignmentRepository(db)

    # ====== 1. Sleep hours (average over past 7 days) ======
    sleep_hours_list = log_repo.get_sleep_hours_last_n_days(user_id, n=7)
    if sleep_hours_list:
        avg_sleep_hours = sum(sleep_hours_list) / len(sleep_hours_list)
    else:
        # Default to recommended if no data
        avg_sleep_hours = 7.0

    # ====== 2. Study std (consistency over past 7 days) ======
    study_by_date = log_repo.get_study_hours_last_n_days(user_id, n=7)
    study_values = list(study_by_date.values())
    if len(study_values) >= 2:
        # Population std (matches thesis §3.6.2)
        mean = sum(study_values) / len(study_values)
        variance = sum((v - mean) ** 2 for v in study_values) / len(study_values)
        study_std = variance ** 0.5
    else:
        study_std = 0.0

    # ====== 3. Workload stats from assignments ======
    upcoming = assignment_repo.list_upcoming(user_id, days=30)

    if not upcoming:
        # No upcoming assignments → minimal risk
        required_hours = 0.0
        days_until_deadline = 30
    else:
        required_hours = sum(float(a.required_hours) for a in upcoming)
        nearest = min(upcoming, key=lambda a: a.deadline)
        now = datetime.now(timezone.utc)
        deadline = nearest.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        delta = deadline - now
        days_until_deadline = max(0, delta.days)

    # ====== 4. Available hours (naive: 6h/day for study) ======
    available_hours = max(1.0, days_until_deadline * 6.0)

    # ====== 5. Call Tier 2 ======
    payload = {
        "sleep_hours": round(avg_sleep_hours, 2),
        "required_hours": round(required_hours, 2),
        "available_hours": round(available_hours, 2),
        "days_until_deadline": days_until_deadline,
        "study_std": round(study_std, 2),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            r = await http.post(
                f"{settings.RISK_API_URL}/api/risk/score",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Risk Indicator service unavailable: {e}",
        ) from e
