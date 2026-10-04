from sqlalchemy.orm import Session
from app.repositories.log_repo import LogRepository
from app.repositories.subject_repo import SubjectRepository
from app.repositories.assignment_repo import AssignmentRepository


class DashboardService:
    def __init__(self, db: Session):
        self.log_repo = LogRepository(db)
        self.subject_repo = SubjectRepository(db)
        self.assignment_repo = AssignmentRepository(db)

    def get_summary(self, user_id: str) -> dict:
        study_by_date = self.log_repo.get_study_hours_last_n_days(user_id, 7)
        sleep_hours = self.log_repo.get_sleep_hours_last_n_days(user_id, 7)

        assignments = self.assignment_repo.list_upcoming(user_id, days=30)
        subjects = self.subject_repo.list_by_user(user_id)

        return {
            "study_hours_by_date": study_by_date,
            "sleep_hours_recent": sleep_hours,
            "upcoming_assignments": [
                {
                    "assignment_id": str(a.assignment_id),
                    "title": a.title,
                    "subject_id": str(a.subject_id),
                    "deadline": a.deadline.isoformat(),
                    "required_hours": float(a.required_hours),
                    "priority": a.priority,
                }
                for a in assignments
            ],
            "subjects": [
                {
                    "subject_id": str(s.subject_id),
                    "subject_name": s.subject_name,
                    "difficulty": s.difficulty,
                    "priority": s.priority,
                }
                for s in subjects
            ],
        }
