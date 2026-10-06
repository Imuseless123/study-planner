from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.orm_models import User
from app.schemas.subjects import (
    SubjectCreate, SubjectUpdate, SubjectResponse, SubjectListResponse,
)
from app.repositories.subject_repo import SubjectRepository

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


def _to_response(s) -> SubjectResponse:
    return SubjectResponse(
        subject_id=str(s.subject_id),
        subject_name=s.subject_name,
        difficulty=s.difficulty,
        priority=s.priority,
    )


@router.get("", response_model=SubjectListResponse)
def list_subjects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = SubjectRepository(db).list_by_user(str(user.user_id))
    return SubjectListResponse(subjects=[_to_response(s) for s in items])


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    req: SubjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = SubjectRepository(db).create(
        str(user.user_id), req.subject_name, req.difficulty, req.priority,
    )
    return _to_response(s)


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = SubjectRepository(db).get_by_id(subject_id, str(user.user_id))
    if not s:
        raise HTTPException(404, "Subject not found")
    return _to_response(s)


@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    req: SubjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = SubjectRepository(db)
    s = repo.get_by_id(subject_id, str(user.user_id))
    if not s:
        raise HTTPException(404, "Subject not found")

    # exclude_unset → chỉ update fields được gửi lên
    updates = req.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "No fields to update")

    s = repo.update(s, **updates)
    return _to_response(s)


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
