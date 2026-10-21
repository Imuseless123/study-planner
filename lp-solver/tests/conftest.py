"""Fixtures for LP Solver tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _standard_slots(n_days: int = 3, hours_per_slot: float = 2.0) -> list[dict]:
    """3 slots per day with tod factors."""
    tods = [1.2, 1.0, 0.8]  # morning, afternoon, evening
    return [
        {"day": d, "slot": t, "tod_factor": tods[t], "available_hours": hours_per_slot}
        for d in range(n_days)
        for t in range(3)
    ]


@pytest.fixture
def thesis_example_payload() -> dict:
    """
    Example from thesis §4.5.6.
    Expected objective value: ≈ 52.0
    """
    return {
        "subjects": [
            {
                "id": "math",
                "required_hours": 4,
                "deadline_day": 0,
                "difficulty": 4,
                "priority": 5,
                "urgency": 1.0,
            },
            {
                "id": "physics",
                "required_hours": 3,
                "deadline_day": 1,
                "difficulty": 3,
                "priority": 4,
                "urgency": 0.5,
            },
        ],
        "time_slots": _standard_slots(3, 2.0),
        "max_daily_hours": 4.0,
        "min_session_hours": 0.5,
        "buffer_ratio": 0.25,
        "big_m": 8.0,
    }


@pytest.fixture
def simple_payload() -> dict:
    """Single subject, single day, easily feasible."""
    return {
        "subjects": [
            {
                "id": "sub1",
                "required_hours": 2,
                "deadline_day": 2,
                "difficulty": 3,
                "priority": 3,
                "urgency": 1 / 3,
            },
        ],
        "time_slots": _standard_slots(3, 2.0),
        "max_daily_hours": 4.0,
    }
