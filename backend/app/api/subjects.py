from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.orm_models import User
from app.schemas.subjects import SubjectCreate, SubjectResponse, SubjectListResponse
from app.repositories.subject_repo import SubjectRepository

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("", response_model=SubjectListResponse)
def list_subjects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = SubjectRepository(db).list_by_user(str(user.user_id))
    return SubjectListResponse(subjects=[
        SubjectResponse(
            subject_id=str(s.subject_id),
            subject_name=s.subject_name,
            difficulty=s.difficulty,
            priority=s.priority,
        ) for s in items
    ])


@router.post("", response_model=SubjectResponse)
def create_subject(
    req: SubjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = SubjectRepository(db).create(
        str(user.user_id), req.subject_name, req.difficulty, req.priority,
    )
    return SubjectResponse(
        subject_id=str(s.subject_id),
        subject_name=s.subject_name,
        difficulty=s.difficulty,
        priority=s.priority,
    )


@router.delete("/{subject_id}")
def delete_subject(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = SubjectRepository(db)
    s = repo.get_by_id(subject_id, str(user.user_id))
    if not s:
        raise HTTPException(404, "Subject not found")
    repo.delete(s)
    return {"status": "ok"}
