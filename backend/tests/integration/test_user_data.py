"""Integration tests for /api/user/data (export + delete)."""
import pytest


@pytest.mark.integration
class TestDataExport:
    def test_export_empty_user(self, client, auth_headers):
        r = client.get("/api/user/data", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["schema_version"] == "1.0"
        assert data["user"]["username"] == "test_user"
        assert data["subjects"] == []
        assert data["stats"]["total_subjects"] == 0

    def test_export_with_full_data(self, client, auth_headers, test_subject,
                                     test_assignment, test_study_session,
                                     test_sleep_log, test_mood_log, test_consent):
        r = client.get("/api/user/data", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()

        assert len(data["subjects"]) == 1
        assert len(data["assignments"]) == 1
        assert len(data["study_sessions"]) == 1
        assert len(data["sleep_logs"]) == 1
        assert len(data["mood_logs"]) == 1
        assert len(data["consents"]) == 1

        # Stats
        assert data["stats"]["total_study_sessions"] == 1
        assert data["stats"]["total_study_hours"] == 2.0
        assert data["stats"]["average_sleep_hours"] == 8.0
        assert data["stats"]["total_subjects"] == 1

    def test_export_requires_auth(self, client):
        r = client.get("/api/user/data")
        assert r.status_code in (401, 403)


@pytest.mark.integration
class TestAccountDeletion:
    def test_delete_requires_confirm_true(self, client, auth_headers, test_user):
        r = client.request(
            "DELETE",
            "/api/user/data",
            json={
                "confirm": False,
                "username_confirmation": "test_user",
            },
            headers=auth_headers,
        )
        assert r.status_code == 400
        assert "confirm=true" in r.json()["detail"]

    def test_delete_requires_matching_username(self, client, auth_headers,
                                                 test_user):
        r = client.request(
            "DELETE",
            "/api/user/data",
            json={
                "confirm": True,
                "username_confirmation": "wrong_username",
            },
            headers=auth_headers,
        )
        assert r.status_code == 400
        assert "does not match" in r.json()["detail"]

    def test_delete_success(self, client, auth_headers, test_user, test_subject,
                             test_study_session, db_session):
        """Full delete flow: user + all data removed."""
        from app.models.orm_models import User, Subject, StudySession

        user_id = test_user.user_id

        r = client.request(
            "DELETE",
            "/api/user/data",
            json={
                "confirm": True,
                "username_confirmation": "test_user",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

        # Verify DB is clean
        assert db_session.query(User).filter(User.user_id == user_id).first() is None
        assert db_session.query(Subject).filter(
            Subject.user_id == user_id
        ).first() is None
        assert db_session.query(StudySession).filter(
            StudySession.user_id == user_id
        ).first() is None
