"""Integration tests for the Risk Indicator API."""
import pytest


@pytest.mark.integration
class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "risk-indicator"

    def test_root_returns_info(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "endpoint" in r.json()


@pytest.mark.integration
class TestRiskEndpoint:
    def test_good_habits_returns_low(self, client, good_habits_payload):
        r = client.post("/api/risk/score", json=good_habits_payload)
        assert r.status_code == 200
        data = r.json()
        assert abs(data["risk_score"] - 11.3) < 0.1
        assert data["level"] == "low"

    def test_high_risk_returns_high(self, client, high_risk_payload):
        r = client.post("/api/risk/score", json=high_risk_payload)
        assert r.status_code == 200
        data = r.json()
        assert abs(data["risk_score"] - 61.7) < 0.1
        assert data["level"] == "high"

    def test_boundary_returns_100(self, client, boundary_payload):
        r = client.post("/api/risk/score", json=boundary_payload)
        assert r.status_code == 200
        assert r.json()["risk_score"] == 100.0

    def test_response_has_disclaimer(self, client, good_habits_payload):
        r = client.post("/api/risk/score", json=good_habits_payload)
        data = r.json()
        assert "disclaimer" in data
        assert len(data["disclaimer"]) > 50
        assert "KHÔNG phải là chẩn đoán" in data["disclaimer"]

    def test_response_has_components(self, client, good_habits_payload):
        r = client.post("/api/risk/score", json=good_habits_payload)
        data = r.json()
        assert "components" in data
        assert "weights" in data
        assert data["weights"]["sleep_deficit"] == 0.35

    def test_required_hours_zero_is_valid(self, client):
        """required_hours=0 means no upcoming work → valid input."""
        r = client.post("/api/risk/score", json={
            "sleep_hours": 8,
            "required_hours": 0,       # ← không còn 422
            "available_hours": 40,
            "days_until_deadline": 30,
            "study_std": 0.5,
        })
        assert r.status_code == 200
        # workload_density = 0/40 = 0 → contributes 0 to score
        assert r.json()["components"]["workload_density"] == 0.0

    def test_validation_sleep_too_high(self, client):
        r = client.post("/api/risk/score", json={
            "sleep_hours": 30,
            "required_hours": 10,
            "available_hours": 40,
            "days_until_deadline": 5,
            "study_std": 1.0,
        })
        assert r.status_code == 422

    def test_validation_negative_required(self, client):
        r = client.post("/api/risk/score", json={
            "sleep_hours": 8,
            "required_hours": -1,      # ← vẫn 422 vì ge=0
            "available_hours": 40,
            "days_until_deadline": 5,
            "study_std": 1.0,
        })
        assert r.status_code == 422

    def test_validation_available_zero(self, client):
        r = client.post("/api/risk/score", json={
            "sleep_hours": 8,
            "required_hours": 10,
            "available_hours": 0,      # ← vẫn 422 vì gt=0
            "days_until_deadline": 5,
            "study_std": 1.0,
        })
        assert r.status_code == 422

    def test_validation_missing_field(self, client):
        r = client.post("/api/risk/score", json={
            "sleep_hours": 8,
        })
        assert r.status_code == 422
