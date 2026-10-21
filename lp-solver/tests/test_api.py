"""API integration tests."""
import pytest


@pytest.mark.integration
class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["service"] == "lp-solver"

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "endpoint" in r.json()


@pytest.mark.integration
class TestGenerateEndpoint:
    def test_thesis_example(self, client, thesis_example_payload):
        r = client.post("/api/schedule/generate", json=thesis_example_payload)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "optimal"
        assert data["feasible"] is True
        assert abs(data["objective_value"] - 52.0) < 2.0
        assert len(data["schedule"]) > 0

    def test_invalid_request_422(self, client):
        r = client.post("/api/schedule/generate", json={
            "subjects": [],  # empty → validation error
            "time_slots": [],
            "max_daily_hours": 4.0,
        })
        assert r.status_code == 422

    def test_missing_field_422(self, client):
        r = client.post("/api/schedule/generate", json={
            "subjects": [{"id": "s1"}],  # missing fields
        })
        assert r.status_code == 422

    def test_response_structure(self, client, thesis_example_payload):
        r = client.post("/api/schedule/generate", json=thesis_example_payload)
        data = r.json()
        assert "schedule" in data
        assert "explanation" in data
        assert "warnings" in data
        assert "objective_value" in data
        assert "per_subject" in data["explanation"]
        assert "per_day" in data["explanation"]
