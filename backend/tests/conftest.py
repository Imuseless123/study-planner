"""
Pytest configuration and shared fixtures.

Test strategy:
- Uses a separate PostgreSQL database (study_planner_test) on same Postgres instance
- Each test function gets a fresh transaction that rolls back at the end
- Reuses migrations from main DB via Alembic
"""
import os
import sys
from pathlib import Path

# Add backend/ to sys.path so we can import 'app'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password, create_access_token
from app.main import app
from app.models.orm_models import (
    Base, User, Subject, Assignment, StudySession, SleepLog, MoodLog, Consent,
)


# ============================================================
# TEST DATABASE
# ============================================================

def _build_test_db_url() -> str:
    """
    Build test DB URL by replacing ONLY the database name
    (last path segment), NOT the username.
    """
    settings = get_settings()
    main_url = settings.DATABASE_URL
    # rsplit("/", 1) → tách ở dấu "/" CUỐI CÙNG
    base, _db_name = main_url.rsplit("/", 1)
    return f"{base}/study_planner_test"


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", _build_test_db_url())


@pytest.fixture(scope="session")
def engine():
    """Create engine once per session."""
    eng = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(engine):
    """Create all tables once at start, drop at end."""
    # Drop all tables first (clean slate)
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Optional cleanup — comment out to keep data for debugging
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """
    Provide a transactional session for a test.
    Rolls back after test to isolate.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    FastAPI TestClient with overridden DB dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================
# USER FIXTURES
# ============================================================

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user in DB."""
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash=hash_password("test_password_123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session: Session) -> User:
    """Create a second user for isolation tests."""
    user = User(
        username="other_user",
        email="other@example.com",
        password_hash=hash_password("other_password_123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Access token for test_user."""
    return create_access_token(str(test_user.user_id))


@pytest.fixture
def second_auth_token(second_user: User) -> str:
    """Access token for second_user."""
    return create_access_token(str(second_user.user_id))


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Headers with Authorization for test_user."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def second_auth_headers(second_auth_token: str) -> dict:
    """Headers with Authorization for second_user."""
    return {"Authorization": f"Bearer {second_auth_token}"}


# ============================================================
# DOMAIN FIXTURES
# ============================================================

@pytest.fixture
def test_consent(db_session: Session, test_user: User) -> Consent:
    """Consent record for test_user."""
    from datetime import datetime, timedelta, timezone

    consent = Consent(
        user_id=test_user.user_id,
        version="1.0",
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)
    return consent


@pytest.fixture
def test_subject(db_session: Session, test_user: User) -> Subject:
    """Sample subject for test_user."""
    subject = Subject(
        user_id=test_user.user_id,
        subject_name="Toán cao cấp",
        difficulty=4,
        priority=5,
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def second_subject(db_session: Session, second_user: User) -> Subject:
    """Sample subject for second_user (isolation test)."""
    subject = Subject(
        user_id=second_user.user_id,
        subject_name="Vật lý",
        difficulty=3,
        priority=4,
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def test_assignment(db_session: Session, test_user: User, test_subject: Subject) -> Assignment:
    """Sample assignment."""
    from datetime import datetime, timedelta, timezone

    assignment = Assignment(
        user_id=test_user.user_id,
        subject_id=test_subject.subject_id,
        title="Bài tập chương 1",
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
        required_hours=4.0,
        priority=5,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


@pytest.fixture
def test_study_session(db_session: Session, test_user: User, test_subject: Subject) -> StudySession:
    """Sample study session."""
    from datetime import datetime, timezone

    session = StudySession(
        user_id=test_user.user_id,
        subject_id=test_subject.subject_id,
        start_time=datetime.now(timezone.utc),
        duration=2.0,
        focus_level=4,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def test_sleep_log(db_session: Session, test_user: User) -> SleepLog:
    """Sample sleep log."""
    from datetime import datetime, timedelta, timezone

    wake_time = datetime.now(timezone.utc)
    sleep_time = wake_time - timedelta(hours=8)

    log = SleepLog(
        user_id=test_user.user_id,
        sleep_time=sleep_time,
        wake_time=wake_time,
        quality=4,
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log


@pytest.fixture
def test_mood_log(db_session: Session, test_user: User) -> MoodLog:
    """Sample mood log."""
    from datetime import date

    log = MoodLog(
        user_id=test_user.user_id,
        log_date=date.today(),
        energy_level=4,
        stress_level=2,
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log
