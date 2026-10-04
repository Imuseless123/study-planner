from sqlalchemy.orm import Session
from app.models.orm_models import Subject


class SubjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: str) -> list[Subject]:
        return self.db.query(Subject).filter(Subject.user_id == user_id).all()

    def get_by_id(self, subject_id: str, user_id: str) -> Subject | None:
        return (
            self.db.query(Subject)
            .filter(Subject.subject_id == subject_id, Subject.user_id == user_id)
            .first()
        )

    def create(self, user_id: str, name: str, difficulty: int, priority: int) -> Subject:
        s = Subject(
            user_id=user_id, subject_name=name,
            difficulty=difficulty, priority=priority,
        )
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def delete(self, subject: Subject) -> None:
        self.db.delete(subject)
        self.db.commit()
