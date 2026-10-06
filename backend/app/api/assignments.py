from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.orm_models import User
from app.schemas.assignments import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentListResponse, AssignmentStatsResponse,
)
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.subject_repo import SubjectRepository

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


def _to_response(a, subject_name: str) -> AssignmentResponse:
    now = datetime.now(timezone.utc)
    # Normalize deadline: nếu naive thì assume UTC
    deadline = a.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    delta = deadline - now
    days_until = delta.days
    is_overdue = deadline < now

    return AssignmentResponse(
        assignment_id=str(a.assignment_id),
        subject_id=str(a.subject_id),
        subject_name=subject_name,
        title=a.title,
        deadline=a.deadline,
        required_hours=float(a.required_hours),
        priority=a.priority,
        days_until_deadline=days_until,
        is_overdue=is_overdue,
    )


def _get_subject_name(db: Session, subject_id: str, user_id: str) -> str:
    s = SubjectRepository(db).get_by_id(subject_id, user_id)
    if not s:
        raise HTTPException(404, "Subject not found")
    return s.subject_name


# ====== LIST ======

@router.get("", response_model=AssignmentListResponse)
def list_assignments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = AssignmentRepository(db).list_all(str(user.user_id))
    return AssignmentListResponse(
        assignments=[_to_response(a, name) for a, name in rows]
    )


@router.get("/stats", response_model=AssignmentStatsResponse)
def get_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = AssignmentRepository(db).list_all(str(user.user_id))
    now = datetime.now(timezone.utc)
    threshold = now + __import__("datetime").timedelta(days=3)

    overdue = 0
    due_soon = 0
    high_priority = 0
    total_hours = 0.0

    for a, _ in rows:
        deadline = a.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if deadline < now:
            overdue += 1
        elif deadline <= threshold:
            due_soon += 1
        if a.priority >= 4:
            high_priority += 1
        total_hours += float(a.required_hours)

    return AssignmentStatsResponse(
        total=len(rows),
        overdue=overdue,
        due_soon=due_soon,
        high_priority=high_priority,
        total_required_hours=round(total_hours, 1),
    )


# ====== CREATE ======

@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    req: AssignmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject_name = _get_subject_name(db, req.subject_id, str(user.user_id))

    # Validate deadline not in past
    deadline = req.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if deadline < datetime.now(timezone.utc):
        raise HTTPException(422, "Deadline must be in the future")

    a = AssignmentRepository(db).create(
        str(user.user_id), req.subject_id, req.title,
        req.deadline, req.required_hours, req.priority,
    )
    return _to_response(a, subject_name)


# ====== GET ONE ======

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = AssignmentRepository(db).get_by_id(assignment_id, str(user.user_id))
    if not a:
        raise HTTPException(404, "Assignment not found")
    subject_name = _get_subject_name(db, str(a.subject_id), str(user.user_id))
    return _to_response(a, subject_name)


# ====== UPDATE ======

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: str,
    req: AssignmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = AssignmentRepository(db)
    a = repo.get_by_id(assignment_id, str(user.user_id))
    if not a:
        raise HTTPException(404, "Assignment not found")

    updates = req.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "No fields to update")

    # Nếu đổi subject_id → verify subject tồn tại và thuộc user
    if "subject_id" in updates and updates["subject_id"]:
        _get_subject_name(db, updates["subject_id"], str(user.user_id))

    # Nếu đổi deadline → verify future (chỉ khi deadline thay đổi)
    if "deadline" in updates and updates["deadline"]:
        new_deadline = updates["deadline"]
        if new_deadline.tzinfo is None:
            new_deadline = new_deadline.replace(tzinfo=timezone.utc)
        if new_deadline < datetime.now(timezone.utc):
            raise HTTPException(422, "Deadline must be in the future")

    a = repo.update(a, **updates)
    subject_name = _get_subject_name(db, str(a.subject_id), str(user.user_id))
    return _to_response(a, subject_name)


# ====== DELETE ======

@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = AssignmentRepository(db)
    a = repo.get_by_id(assignment_id, str(user.user_id))
    if not a:
        raise HTTPException(404, "Assignment not found")
    repo.delete(a)
    return {"status": "ok"}
