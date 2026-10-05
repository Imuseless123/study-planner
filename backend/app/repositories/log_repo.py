from datetime import datetime, timedelta, date
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.orm_models import StudySession, SleepLog, MoodLog, Subject


class LogRepository:
    def __init__(self, db: Session):
        self.db = db

    # ====== CREATE ======

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

    # ====== LIST ======

    def list_study_sessions(self, user_id: str, limit: int = 50) -> list[dict]:
        rows = (
            self.db.query(StudySession, Subject.subject_name)
            .join(Subject, Subject.subject_id == StudySession.subject_id)
            .filter(StudySession.user_id == user_id)
            .order_by(StudySession.start_time.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "session_id": str(s.session_id),
                "subject_id": str(s.subject_id),
                "subject_name": name,
                "start_time": s.start_time,
                "duration": float(s.duration),
                "focus_level": s.focus_level,
            }
            for s, name in rows
        ]

    def list_sleep_logs(self, user_id: str, limit: int = 50) -> list[dict]:
        rows = (
            self.db.query(SleepLog)
            .filter(SleepLog.user_id == user_id)
            .order_by(SleepLog.sleep_time.desc())
            .limit(limit)
            .all()
        )
        result = []
        for s in rows:
            hours = (s.wake_time - s.sleep_time).total_seconds() / 3600.0
            result.append({
                "sleep_id": str(s.sleep_id),
                "sleep_time": s.sleep_time,
                "wake_time": s.wake_time,
                "quality": s.quality,
                "hours": round(hours, 2),
            })
        return result

    def list_mood_logs(self, user_id: str, limit: int = 50) -> list[dict]:
        rows = (
            self.db.query(MoodLog)
            .filter(MoodLog.user_id == user_id)
            .order_by(MoodLog.log_date.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "mood_id": str(m.mood_id),
                "log_date": m.log_date,
                "energy_level": m.energy_level,
                "stress_level": m.stress_level,
            }
            for m in rows
        ]

    # ====== DELETE ======

    def delete_study_session(self, session_id: str, user_id: str) -> bool:
        s = (
            self.db.query(StudySession)
            .filter(StudySession.session_id == session_id, StudySession.user_id == user_id)
            .first()
        )
        if not s:
            return False
        self.db.delete(s)
        self.db.commit()
        return True

    def delete_sleep_log(self, sleep_id: str, user_id: str) -> bool:
        s = (
            self.db.query(SleepLog)
            .filter(SleepLog.sleep_id == sleep_id, SleepLog.user_id == user_id)
            .first()
        )
        if not s:
            return False
        self.db.delete(s)
        self.db.commit()
        return True

    def delete_mood_log(self, mood_id: str, user_id: str) -> bool:
        m = (
            self.db.query(MoodLog)
            .filter(MoodLog.mood_id == mood_id, MoodLog.user_id == user_id)
            .first()
        )
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True

    # ====== AGGREGATIONS (cho dashboard) ======

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

    def get_study_hours_matrix(self, user_id: str, n: int = 7) -> dict:
        """Return {date: {subject_name: hours}} cho heatmap."""
        cutoff = datetime.utcnow() - timedelta(days=n)
        rows = (
            self.db.query(
                func.date(StudySession.start_time).label("d"),
                Subject.subject_name.label("sub"),
                func.sum(StudySession.duration).label("total"),
            )
            .join(Subject, Subject.subject_id == StudySession.subject_id)
            .filter(StudySession.user_id == user_id, StudySession.start_time >= cutoff)
            .group_by(func.date(StudySession.start_time), Subject.subject_name)
            .all()
        )
        matrix: dict = {}
        for r in rows:
            date_key = str(r.d)
            if date_key not in matrix:
                matrix[date_key] = {}
            matrix[date_key][r.sub] = float(r.total or 0)
        return matrix
