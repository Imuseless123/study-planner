"""Service to generate schedule via Tier 3 (LP Solver)."""
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.orm_models import Assignment, Subject, Schedule
from app.services.risk_service import fetch_risk_score

settings = get_settings()

# Risk → W_max adjustment (thesis §4.5.5)
ALPHA = 0.5
DEFAULT_W_MAX = 6.0
DEFAULT_HORIZON_DAYS = 7
MAX_HORIZON_DAYS = 30
HOURS_PER_SLOT = 2.0
TOD_FACTORS = [1.2, 1.0, 0.8]  # morning, afternoon, evening


async def _call_lp_solver(payload: dict) -> dict:
    """POST to Tier 3 /api/schedule/generate."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            r = await http.post(
                f"{settings.LP_SOLVER_API_URL}/api/schedule/generate",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LP Solver service unavailable: {e}",
        ) from e


def _aggregate_subjects(
    user_id: str, db: Session,
) -> tuple[list[dict], int]:
    """
    Aggregate assignments into LP subjects.

    Each assignment → one entry (id = assignment_id).
    difficulty + priority từ parent subject.
    deadline_day = days from now (UTC).
    """
    now = datetime.now(timezone.utc)

    assignments = (
        db.query(Assignment)
        .filter(
            Assignment.user_id == user_id,
            Assignment.deadline > now,
        )
        .order_by(Assignment.deadline.asc())
        .all()
    )

    if not assignments:
        return [], 0

    subjects_by_id = {
        str(s.subject_id): s
        for s in db.query(Subject).filter(Subject.user_id == user_id).all()
    }

    subjects_input = []
    max_deadline_day = 0

    for a in assignments:
        subject = subjects_by_id.get(str(a.subject_id))
        if not subject:
            continue

        deadline = a.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        deadline_day = max(0, (deadline - now).days)
        max_deadline_day = max(max_deadline_day, deadline_day)

        subjects_input.append({
            "id": str(a.assignment_id),
            "required_hours": float(a.required_hours),
            "deadline_day": deadline_day,
            "difficulty": subject.difficulty,
            "priority": a.priority,
            # urgency auto-computed by Tier 3
        })

    return subjects_input, max_deadline_day


def _build_time_slots(horizon: int) -> list[dict]:
    """3 slots/day × horizon days, with tod factors."""
    return [
        {
            "day": d,
            "slot": t,
            "tod_factor": TOD_FACTORS[t],
            "available_hours": HOURS_PER_SLOT,
        }
        for d in range(horizon)
        for t in range(3)
    ]


async def generate_schedule_for_user(user_id: str, db: Session) -> dict:
    """
    Full pipeline:
    1. Aggregate assignments → subjects
    2. Get risk score from Tier 2
    3. Compute W_max_effective
    4. Build time slots
    5. Call Tier 3
    6. Fallback with original W_max if infeasible
    7. Save to DB
    """
    # 1. Aggregate assignments
    subjects_input, max_deadline_day = _aggregate_subjects(user_id, db)

    if not subjects_input:
        return {
            "status": "no_assignments",
            "feasible": False,
            "schedule": [],
            "warnings": [{
                "type": "no_assignments",
                "message": (
                    "Bạn chưa có bài tập nào có deadline trong tương lai. "
                    "Hãy tạo bài tập ở trang Bài tập trước."
                ),
            }],
        }

    # 2. Risk score (Tier 2)
    risk = await fetch_risk_score(user_id, db)
    risk_score = float(risk["risk_score"])

    # 3. W_max_effective (thesis §4.5.5)
    w_max_eff = DEFAULT_W_MAX * (1 - ALPHA * risk_score / 100.0)
    w_max_eff = max(0.5, w_max_eff)  # safety floor

    # 4. Time slots
    horizon = min(max(DEFAULT_HORIZON_DAYS, max_deadline_day + 1), MAX_HORIZON_DAYS)
    time_slots = _build_time_slots(horizon)

    # 5. Call Tier 3 (lần 1)
    payload = {
        "subjects": subjects_input,
        "time_slots": time_slots,
        "max_daily_hours": round(w_max_eff, 2),
        "min_session_hours": 0.5,
        "buffer_ratio": 0.25,
        "big_m": 8.0,
    }
    result = await _call_lp_solver(payload)

    # 6. Fallback: nếu Infeasible, retry với W_max gốc
    if not result.get("feasible", False):
        payload_fb = {**payload, "max_daily_hours": DEFAULT_W_MAX}
        result_fb = await _call_lp_solver(payload_fb)
        if result_fb.get("feasible", False):
            result = result_fb
            result.setdefault("warnings", []).append({
                "type": "risk_override",
                "message": (
                    f"Lịch được tạo vượt mức giờ khuyến nghị do rủi ro cao "
                    f"(W_max_effective = {w_max_eff:.1f}h). "
                    f"Vui lòng cân nhắc giảm số bài tập hoặc dời deadline."
                ),
            })

    # 7. Save to DB
    schedule_record = Schedule(
        user_id=user_id,
        schedule_data=result,
        feasible=result.get("feasible", False),
        risk_score_at_generation=risk_score,
        warnings=result.get("warnings") or None,
    )
    db.add(schedule_record)
    db.commit()
    db.refresh(schedule_record)

    # Augment response with metadata
    result["schedule_id"] = str(schedule_record.schedule_id)
    result["risk_score_at_generation"] = risk_score
    result["risk_level"] = risk.get("level")
    result["w_max_effective"] = round(w_max_eff, 2)
    result["w_max"] = DEFAULT_W_MAX
    result["horizon_days"] = horizon

    return result


def get_latest_schedule(user_id: str, db: Session) -> dict | None:
    """Lấy schedule gần nhất của user."""
    record = (
        db.query(Schedule)
        .filter(Schedule.user_id == user_id)
        .order_by(Schedule.generated_date.desc())
        .first()
    )
    if not record:
        return None

    data = dict(record.schedule_data or {})
    data["schedule_id"] = str(record.schedule_id)
    data["generated_date"] = record.generated_date.isoformat()
    data["risk_score_at_generation"] = (
        float(record.risk_score_at_generation)
        if record.risk_score_at_generation is not None
        else None
    )
    return data
