"""Unit tests for Pydantic schemas — validation."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.subjects import SubjectCreate, SubjectUpdate
from app.schemas.assignments import AssignmentCreate, AssignmentUpdate


@pytest.mark.unit
class TestAuthSchemas:
    def test_register_valid(self):
        req = RegisterRequest(
            username="alice", password="password123", email="a@b.com"
        )
        assert req.username == "alice"

    def test_register_username_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="ab", password="password123", email="a@b.com")

    def test_register_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="alice", password="password123", email="not-email")

    def test_register_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="alice", password="short", email="a@b.com")


@pytest.mark.unit
class TestSubjectSchemas:
    def test_subject_create_valid(self):
        s = SubjectCreate(subject_name="Math", difficulty=3, priority=5)
        assert s.difficulty == 3

    def test_difficulty_out_of_range(self):
        with pytest.raises(ValidationError):
            SubjectCreate(subject_name="Math", difficulty=6, priority=3)

    def test_difficulty_zero(self):
        with pytest.raises(ValidationError):
            SubjectCreate(subject_name="Math", difficulty=0, priority=3)

    def test_update_all_optional(self):
        s = SubjectUpdate()
        assert s.subject_name is None
        assert s.difficulty is None

    def test_update_partial(self):
        s = SubjectUpdate(difficulty=5)
        assert s.difficulty == 5
        assert s.subject_name is None


@pytest.mark.unit
class TestAssignmentSchemas:
    def test_assignment_create_valid(self):
        a = AssignmentCreate(
            subject_id="some-uuid",
            title="HW1",
            deadline=datetime.now(timezone.utc),
            required_hours=4.0,
            priority=5,
        )
        assert a.title == "HW1"

    def test_required_hours_negative(self):
        with pytest.raises(ValidationError):
            AssignmentCreate(
                subject_id="x", title="HW", deadline=datetime.now(timezone.utc),
                required_hours=-1.0, priority=3,
            )

    def test_required_hours_exceeds_max(self):
        with pytest.raises(ValidationError):
            AssignmentCreate(
                subject_id="x", title="HW", deadline=datetime.now(timezone.utc),
                required_hours=200.0, priority=3,
            )
