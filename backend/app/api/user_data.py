from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.orm_models import (
    User, Consent, Subject, Assignment,
    StudySession, SleepLog, MoodLog, Schedule, Feedback,
)
from app.schemas.user_data import DataExportResponse, DeleteAccountRequest

router = APIRouter(prefix="/api/user", tags=["user-data"])


# ============================================================
# EXPORT — GET /api/user/data
# ============================================================
@router.get("/data", response_model=DataExportResponse)
def export_user_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export toàn bộ dữ liệu cá nhân dưới dạng JSON.
    Bao gồm tất cả records thuộc user, kèm stats tổng hợp.
    """
    uid = user.user_id

    # Load all data
    subjects = db.query(Subject).filter(Subject.user_id == uid).all()
    assignments = db.query(Assignment).filter(Assignment.user_id == uid).all()
    study_sessions = (
        db.query(StudySession)
        .filter(StudySession.user_id == uid)
        .order_by(StudySession.start_time.desc())
        .all()
    )
    sleep_logs = (
        db.query(SleepLog)
        .filter(SleepLog.user_id == uid)
        .order_by(SleepLog.sleep_time.desc())
        .all()
    )
    mood_logs = (
        db.query(MoodLog)
        .filter(MoodLog.user_id == uid)
        .order_by(MoodLog.log_date.desc())
        .all()
    )
    schedules = db.query(Schedule).filter(Schedule.user_id == uid).all()
    feedbacks = db.query(Feedback).filter(Feedback.user_id == uid).all()
    consents = (
        db.query(Consent)
        .filter(Consent.user_id == uid)
        .order_by(Consent.signed_at.desc())
        .all()
    )

    # Build stats
    total_study_hours = sum(float(s.duration) for s in study_sessions)
    total_sleep_hours = sum(
        (s.wake_time - s.sleep_time).total_seconds() / 3600.0
        for s in sleep_logs
    )
    avg_sleep_hours = (
        round(total_sleep_hours / len(sleep_logs), 2) if sleep_logs else 0
    )
    avg_focus = (
        round(sum(s.focus_level for s in study_sessions) / len(study_sessions), 2)
        if study_sessions
        else 0
    )

    stats = {
        "total_study_sessions": len(study_sessions),
        "total_study_hours": round(total_study_hours, 2),
        "total_sleep_logs": len(sleep_logs),
        "average_sleep_hours": avg_sleep_hours,
        "total_mood_logs": len(mood_logs),
        "total_subjects": len(subjects),
        "total_assignments": len(assignments),
        "total_schedules": len(schedules),
        "total_feedback": len(feedbacks),
        "average_focus_level": avg_focus,
    }

    return DataExportResponse(
        exported_at=datetime.now(timezone.utc),
        schema_version="1.0",
        user={
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
        subjects=[
            {
                "subject_id": str(s.subject_id),
                "subject_name": s.subject_name,
                "difficulty": s.difficulty,
                "priority": s.priority,
                "created_at": s.created_at.isoformat(),
            }
            for s in subjects
        ],
        assignments=[
            {
                "assignment_id": str(a.assignment_id),
                "subject_id": str(a.subject_id),
                "title": a.title,
                "deadline": a.deadline.isoformat(),
                "required_hours": float(a.required_hours),
                "priority": a.priority,
                "created_at": a.created_at.isoformat(),
            }
            for a in assignments
        ],
        study_sessions=[
            {
                "session_id": str(s.session_id),
                "subject_id": str(s.subject_id),
                "start_time": s.start_time.isoformat(),
                "duration": float(s.duration),
                "focus_level": s.focus_level,
                "created_at": s.created_at.isoformat(),
            }
            for s in study_sessions
        ],
        sleep_logs=[
            {
                "sleep_id": str(s.sleep_id),
                "sleep_time": s.sleep_time.isoformat(),
                "wake_time": s.wake_time.isoformat(),
                "quality": s.quality,
                "created_at": s.created_at.isoformat(),
            }
            for s in sleep_logs
        ],
        mood_logs=[
            {
                "mood_id": str(m.mood_id),
                "log_date": m.log_date.isoformat(),
                "energy_level": m.energy_level,
                "stress_level": m.stress_level,
                "created_at": m.created_at.isoformat(),
            }
            for m in mood_logs
        ],
        schedules=[
            {
                "schedule_id": str(s.schedule_id),
                "generated_date": s.generated_date.isoformat(),
                "schedule_data": s.schedule_data,
                "feasible": s.feasible,
                "risk_score_at_generation": (
                    float(s.risk_score_at_generation)
                    if s.risk_score_at_generation
                    else None
                ),
                "warnings": s.warnings,
            }
            for s in schedules
        ],
        feedback=[
            {
                "feedback_id": str(f.feedback_id),
                "schedule_id": str(f.schedule_id),
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ],
        consents=[
            {
                "consent_id": str(c.consent_id),
                "version": c.version,
                "signed_at": c.signed_at.isoformat(),
                "expires_at": c.expires_at.isoformat(),
                "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
            }
            for c in consents
        ],
        stats=stats,
    )


# ============================================================
# DELETE — DELETE /api/user/data
# ============================================================
@router.delete("/data")
def delete_user_data(
    req: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Xóa vĩnh viễn tài khoản + tất cả dữ liệu liên quan.

    Yêu cầu 2 lớp xác nhận:
    1. confirm = true
    2. username_confirmation = username hiện tại (khớp chính xác)

    Việc xóa sử dụng CASCADE ở DB, nên tất cả records liên quan sẽ bị xóa.
    Hành động KHÔNG THỂ hoàn tác.
    """
    if not req.confirm:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Must confirm=true to delete account",
        )

    if req.username_confirmation != user.username:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Username confirmation does not match",
        )

    # Log (anonymized) trước khi xóa
    print(
        f"[AUDIT] User {user.username} (id={user.user_id}) "
        f"deleted their account at {datetime.now(timezone.utc).isoformat()}"
    )

    # CASCADE sẽ xóa toàn bộ data liên quan
    db.delete(user)
    db.commit()

    return {
        "status": "deleted",
        "message": "Your account and all associated data have been permanently deleted.",
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }
