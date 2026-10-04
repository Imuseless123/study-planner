from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.orm_models import StudySession, SleepLog, MoodLog


class LogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_study_session(self, user_id, subject_id, start_time, duration, focus) -> StudySession:
        s = StudySession(
            user_id=user_id, subject_id=subject_id,
            start_time=start_time, duration=duration, focus_level=focus,
        )
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def create_sleep_log(self, user_id, sleep_time, wake_time, quality) -> SleepLog:
        s = SleepLog(
            user_id=user_id, sleep_time=sleep_time,
            wake_time=wake_time, quality=quality,
        )
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def upsert_mood_log(self, user_id, log_date, energy, stress) -> MoodLog:
        existing = (
            self.db.query(MoodLog)
            .filter(MoodLog.user_id == user_id, MoodLog.log_date == log_date)
            .first()
        )
        if existing:
            existing.energy_level = energy
            existing.stress_level = stress
            self.db.commit()
            self.db.refresh(existing)
            return existing

        m = MoodLog(user_id=user_id, log_date=log_date,
                    energy_level=energy, stress_level=stress)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def get_study_hours_last_n_days(self, user_id: str, n: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=n)
        rows = (
            self.db.query(
                func.date(StudySession.start_time).label("d"),
                func.sum(StudySession.duration).label("total"),
            )
            .filter(StudySession.user_id == user_id, StudySession.start_time >= cutoff)
            .group_by(func.date(StudySession.start_time))
            .all()
        )
        return {str(r.d): float(r.total or 0) for r in rows}

    def get_sleep_hours_last_n_days(self, user_id: str, n: int = 7) -> list[float]:
        cutoff = datetime.utcnow() - timedelta(days=n)
        logs = (
            self.db.query(SleepLog)
            .filter(SleepLog.user_id == user_id, SleepLog.sleep_time >= cutoff)
            .all()
        )
        return [
            (log.wake_time - log.sleep_time).total_seconds() / 3600.0
            for log in logs
        ]
