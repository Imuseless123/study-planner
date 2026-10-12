"""Integration tests for /api/log endpoints."""
import pytest
from datetime import datetime, date, timedelta, timezone


@pytest.mark.integration
class TestStudyLog:
    def test_create_study_log(self, client, auth_headers, test_subject):
        r = client.post("/api/log/study", json={
            "subject_id": str(test_subject.subject_id),
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration": 2.5,
            "focus_level": 4,
        }, headers=auth_headers)
        assert r.status_code == 200
        assert "session_id" in r.json()

    def test_create_study_log_invalid_subject(self, client, auth_headers):
        r = client.post("/api/log/study", json={
            "subject_id": "00000000-0000-0000-0000-000000000000",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration": 2.5,
            "focus_level": 4,
        }, headers=auth_headers)
        assert r.status_code == 404

    def test_create_study_log_invalid_focus(self, client, auth_headers, test_subject):
        r = client.post("/api/log/study", json={
            "subject_id": str(test_subject.subject_id),
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration": 2.5,
            "focus_level": 10,  # > 5
        }, headers=auth_headers)
        assert r.status_code == 422

    def test_list_study_logs(self, client, auth_headers, test_study_session):
        r = client.get("/api/log/study", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert data["items"][0]["subject_name"] == "Toán cao cấp"

    def test_delete_study_log(self, client, auth_headers, test_study_session):
        r = client.delete(
            f"/api/log/study/{test_study_session.session_id}",
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_delete_study_log_wrong_user(
        self, client, second_auth_headers, test_study_session
    ):
        """User B cannot delete User A's log."""
        r = client.delete(
            f"/api/log/study/{test_study_session.session_id}",
            headers=second_auth_headers,
        )
        assert r.status_code == 404


@pytest.mark.integration
class TestSleepLog:
    def test_create_sleep_log(self, client, auth_headers):
        wake = datetime.now(timezone.utc)
        sleep = wake - timedelta(hours=8)
        r = client.post("/api/log/sleep", json={
            "sleep_time": sleep.isoformat(),
            "wake_time": wake.isoformat(),
            "quality": 4,
        }, headers=auth_headers)
        assert r.status_code == 200
        assert "sleep_id" in r.json()

    def test_wake_before_sleep_rejected(self, client, auth_headers):
        now = datetime.now(timezone.utc)
        r = client.post("/api/log/sleep", json={
            "sleep_time": now.isoformat(),
            "wake_time": (now - timedelta(hours=1)).isoformat(),
            "quality": 4,
        }, headers=auth_headers)
        assert r.status_code == 422

    def test_list_sleep_logs_has_hours(self, client, auth_headers, test_sleep_log):
        r = client.get("/api/log/sleep", headers=auth_headers)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        assert items[0]["hours"] == 8.0


@pytest.mark.integration
class TestMoodLog:
    def test_create_mood_log(self, client, auth_headers):
        r = client.post("/api/log/mood", json={
            "log_date": date.today().isoformat(),
            "energy_level": 4,
            "stress_level": 2,
        }, headers=auth_headers)
        assert r.status_code == 200

    def test_mood_upsert_same_day(self, client, auth_headers):
        """Second POST same day should update, not create new."""
        payload = {
            "log_date": date.today().isoformat(),
            "energy_level": 4,
            "stress_level": 2,
        }
        r1 = client.post("/api/log/mood", json=payload, headers=auth_headers)
        assert r1.status_code == 200
        first_id = r1.json()["mood_id"]

        payload["energy_level"] = 2
        payload["stress_level"] = 5
        r2 = client.post("/api/log/mood", json=payload, headers=auth_headers)
        assert r2.json()["mood_id"] == first_id  # same record
