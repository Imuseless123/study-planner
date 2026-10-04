from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.orm_models import User
from app.schemas.logs import (
    StudyLogRequest, StudyLogResponse,
    SleepLogRequest, SleepLogResponse,
    MoodLogRequest, MoodLogResponse,
)
from app.repositories.log_repo import LogRepository
from app.repositories.subject_repo import SubjectRepository

router = APIRouter(prefix="/api/log", tags=["logs"])


@router.post("/study", response_model=StudyLogResponse)
def log_study(
    req: StudyLogRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not SubjectRepository(db).get_by_id(req.subject_id, str(user.user_id)):
        raise HTTPException(404, "Subject not found")
    s = LogRepository(db).create_study_session(
        str(user.user_id), req.subject_id,
        req.start_time, req.duration, req.focus_level,
    )
    return StudyLogResponse(status="ok", session_id=str(s.session_id))


@router.post("/sleep", response_model=SleepLogResponse)
def log_sleep(
    req: SleepLogRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.wake_time <= req.sleep_time:
        raise HTTPException(422, "wake_time must be after sleep_time")
    s = LogRepository(db).create_sleep_log(
        str(user.user_id), req.sleep_time, req.wake_time, req.quality,
    )
    return SleepLogResponse(status="ok", sleep_id=str(s.sleep_id))


@router.post("/mood", response_model=MoodLogResponse)
def log_mood(
    req: MoodLogRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = LogRepository(db).upsert_mood_log(
        str(user.user_id), req.log_date, req.energy_level, req.stress_level,
    )
    return MoodLogResponse(status="ok", mood_id=str(m.mood_id))
