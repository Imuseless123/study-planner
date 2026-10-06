from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.orm_models import Assignment, Subject


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, user_id: str) -> list[tuple[Assignment, str]]:
        """Trả về list (Assignment, subject_name)."""
        return (
            self.db.query(Assignment, Subject.subject_name)
            .join(Subject, Subject.subject_id == Assignment.subject_id)
            .filter(Assignment.user_id == user_id)
            .order_by(Assignment.deadline.asc())
            .all()
        )

    def list_upcoming(self, user_id: str, days: int = 30) -> list[Assignment]:
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)
        return (
            self.db.query(Assignment)
            .filter(
                Assignment.user_id == user_id,
                Assignment.deadline >= now,
                Assignment.deadline <= cutoff,
            )
            .order_by(Assignment.deadline.asc())
            .all()
        )

    def get_by_id(self, assignment_id: str, user_id: str) -> Assignment | None:
        return (
            self.db.query(Assignment)
            .filter(
                Assignment.assignment_id == assignment_id,
                Assignment.user_id == user_id,
            )
            .first()
        )

    def create(
        self, user_id, subject_id, title, deadline, required_hours, priority
    ) -> Assignment:
        a = Assignment(
            user_id=user_id,
            subject_id=subject_id,
            title=title,
            deadline=deadline,
            required_hours=required_hours,
            priority=priority,
        )
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def update(self, assignment: Assignment, **fields) -> Assignment:
        for key, value in fields.items():
            if value is not None and hasattr(assignment, key):
                setattr(assignment, key, value)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def delete(self, assignment: Assignment) -> None:
        self.db.delete(assignment)
        self.db.commit()
