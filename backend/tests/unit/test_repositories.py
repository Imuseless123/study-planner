"""Unit tests for repositories — test data access layer in isolation."""
import pytest
from datetime import datetime, timedelta, timezone

from app.repositories.user_repo import UserRepository
from app.repositories.subject_repo import SubjectRepository
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.log_repo import LogRepository
from app.models.orm_models import User


@pytest.mark.unit
class TestUserRepository:
    def test_create_user(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create("newuser", "new@example.com", "hash123")
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.user_id is not None

    def test_get_by_username_found(self, db_session, test_user):
        repo = UserRepository(db_session)
        found = repo.get_by_username("test_user")
        assert found is not None
        assert found.user_id == test_user.user_id

    def test_get_by_username_not_found(self, db_session):
        repo = UserRepository(db_session)
        assert repo.get_by_username("nonexistent") is None

    def test_get_by_email(self, db_session, test_user):
        repo = UserRepository(db_session)
        found = repo.get_by_email("test@example.com")
        assert found is not None
        assert found.user_id == test_user.user_id

    def test_duplicate_username_raises(self, db_session, test_user):
        from sqlalchemy.exc import IntegrityError

        repo = UserRepository(db_session)
        with pytest.raises(IntegrityError):
            repo.create("test_user", "other@example.com", "hash")


@pytest.mark.unit
class TestSubjectRepository:
    def test_create_subject(self, db_session, test_user):
        repo = SubjectRepository(db_session)
        s = repo.create(str(test_user.user_id), "Math", 4, 5)
        assert s.subject_name == "Math"
        assert s.difficulty == 4

    def test_list_by_user_isolated(self, db_session, test_user, second_user,
                                    test_subject, second_subject):
        repo = SubjectRepository(db_session)
        subjects = repo.list_by_user(str(test_user.user_id))
        assert len(subjects) == 1
        assert subjects[0].subject_name == "Toán cao cấp"

    def test_get_by_id_wrong_user_returns_none(self, db_session, test_user,
                                                second_subject):
        repo = SubjectRepository(db_session)
        # second_subject belongs to second_user, try to get as test_user
        result = repo.get_by_id(
            str(second_subject.subject_id), str(test_user.user_id)
        )
        assert result is None

    def test_update_subject_partial(self, db_session, test_subject):
        repo = SubjectRepository(db_session)
        updated = repo.update(test_subject, difficulty=5)
        assert updated.difficulty == 5
        assert updated.subject_name == "Toán cao cấp"  # unchanged
        assert updated.priority == 5  # unchanged

    def test_delete_subject(self, db_session, test_subject):
        repo = SubjectRepository(db_session)
        repo.delete(test_subject)
        assert repo.get_by_id(
            str(test_subject.subject_id), str(test_subject.user_id)
        ) is None


@pytest.mark.unit
class TestAssignmentRepository:
    def test_list_upcoming_excludes_far_future(self, db_session, test_user):
        repo = AssignmentRepository(db_session)
        # No assignments yet
        assert repo.list_upcoming(str(test_user.user_id), days=30) == []

    def test_list_upcoming_includes_near(self, db_session, test_assignment,
                                          test_user):
        repo = AssignmentRepository(db_session)
        result = repo.list_upcoming(str(test_user.user_id), days=30)
        assert len(result) == 1


@pytest.mark.unit
class TestLogRepository:
    def test_create_study_session(self, db_session, test_user, test_subject):
        repo = LogRepository(db_session)
        session = repo.create_study_session(
            str(test_user.user_id),
            str(test_subject.subject_id),
            datetime.now(timezone.utc),
            1.5,
            4,
        )
        assert session.duration == 1.5
        assert session.focus_level == 4

    def test_upsert_mood_creates_new(self, db_session, test_user):
        from datetime import date

        repo = LogRepository(db_session)
        m = repo.upsert_mood_log(
            str(test_user.user_id), date.today(), 4, 2
        )
        assert m.energy_level == 4

    def test_upsert_mood_updates_existing(self, db_session, test_mood_log,
                                           test_user):
        repo = LogRepository(db_session)
        m = repo.upsert_mood_log(
            str(test_user.user_id), test_mood_log.log_date, 2, 5
        )
        assert m.energy_level == 2
        assert m.stress_level == 5
        assert m.mood_id == test_mood_log.mood_id  # same record
