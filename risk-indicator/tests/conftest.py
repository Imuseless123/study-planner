"""Pytest fixtures for Risk Indicator tests."""
import sys
from pathlib import Path

# Add risk-indicator/ to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def good_habits_payload() -> dict:
    """Scenario: student with good study habits (low risk)."""
    return {
        "sleep_hours": 8,
        "required_hours": 10,
        "available_hours": 40,
        "days_until_deadline": 14,
        "study_std": 0.49,
    }


@pytest.fixture
def high_risk_payload() -> dict:
    """Scenario: student with high risk (high workload, low sleep)."""
    return {
        "sleep_hours": 5,
        "required_hours": 30,
        "available_hours": 40,
        "days_until_deadline": 2,
        "study_std": 3.06,
    }


@pytest.fixture
def boundary_payload() -> dict:
    """Scenario: all components at maximum (score = 100)."""
    return {
        "sleep_hours": 3,       # 4h deficit → SD = 1.0
        "required_hours": 40,   # = available → WD = 1.0
        "available_hours": 40,
        "days_until_deadline": 0,  # DP = 1.0
        "study_std": 3.0,       # SI = 1.0
    }
