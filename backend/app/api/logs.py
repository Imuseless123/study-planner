from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.orm_models import User
from app.schemas.logs import (
    StudyLogRequest, StudyLogResponse,
    SleepLogRequest, SleepLogResponse,
    MoodLogRequest, MoodLogResponse,
    StudyLogListResponse, SleepLogListResponse, MoodLogListResponse,
)
from app.repositories.log_repo import LogRepository
from app.repositories.subject_repo import SubjectRepository

router = APIRouter(prefix="/api/log", tags=["logs"])


# ====== STUDY ======

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


@router.get("/study", response_model=StudyLogListResponse)
def list_study(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = LogRepository(db).list_study_sessions(str(user.user_id), limit=limit)
    return StudyLogListResponse(items=items, total=len(items))


@router.delete("/study/{session_id}")
def delete_study(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not LogRepository(db).delete_study_session(session_id, str(user.user_id)):
        raise HTTPException(404, "Study session not found")
    return {"status": "ok"}


# ====== SLEEP ======

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


@router.get("/sleep", response_model=SleepLogListResponse)
def list_sleep(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = LogRepository(db).list_sleep_logs(str(user.user_id), limit=limit)
    return SleepLogListResponse(items=items, total=len(items))


@router.delete("/sleep/{sleep_id}")
def delete_sleep(
    sleep_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not LogRepository(db).delete_sleep_log(sleep_id, str(user.user_id)):
        raise HTTPException(404, "Sleep log not found")
    return {"status": "ok"}


# ====== MOOD ======

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


@router.get("/mood", response_model=MoodLogListResponse)
def list_mood(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = LogRepository(db).list_mood_logs(str(user.user_id), limit=limit)
    return MoodLogListResponse(items=items, total=len(items))


@router.delete("/mood/{mood_id}")
def delete_mood(
    mood_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not LogRepository(db).delete_mood_log(mood_id, str(user.user_id)):
        raise HTTPException(404, "Mood log not found")
    return {"status": "ok"}
