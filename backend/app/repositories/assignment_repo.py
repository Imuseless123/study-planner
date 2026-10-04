from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.orm_models import Assignment


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_upcoming(self, user_id: str, days: int = 30) -> list[Assignment]:
        now = datetime.utcnow()
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
            .filter(Assignment.assignment_id == assignment_id, Assignment.user_id == user_id)
            .first()
        )

    def create(self, user_id, subject_id, title, deadline, required_hours, priority) -> Assignment:
        a = Assignment(
            user_id=user_id, subject_id=subject_id, title=title,
            deadline=deadline, required_hours=required_hours, priority=priority,
        )
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a
