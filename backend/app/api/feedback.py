"""Feedback endpoints — user rates generated schedules (FR #13)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.orm_models import User, Schedule, Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def create_feedback(
    req: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify schedule belongs to user
    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.schedule_id == req.schedule_id,
            Schedule.user_id == user.user_id,
        )
        .first()
    )
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    fb = Feedback(
        schedule_id=req.schedule_id,
        user_id=user.user_id,
        rating=req.rating,
        comment=req.comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    return FeedbackResponse(
        feedback_id=str(fb.feedback_id),
        schedule_id=str(fb.schedule_id),
        rating=fb.rating,
        comment=fb.comment,
        created_at=fb.created_at,
    )


@router.get("/{schedule_id}", response_model=list[FeedbackResponse])
def list_feedback(
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Feedback)
        .filter(
            Feedback.schedule_id == schedule_id,
            Feedback.user_id == user.user_id,
        )
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return [
        FeedbackResponse(
            feedback_id=str(f.feedback_id),
            schedule_id=str(f.schedule_id),
            rating=f.rating,
            comment=f.comment,
            created_at=f.created_at,
        )
        for f in items
    ]
