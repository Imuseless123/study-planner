"""Integration tests for /api/dashboard/summary."""
import pytest


@pytest.mark.integration
class TestDashboardSummary:
    def test_empty_dashboard(self, client, auth_headers):
        r = client.get("/api/dashboard/summary", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["study_hours_by_date"] == {}
        assert data["study_hours_matrix"] == {}
        assert data["sleep_hours_recent"] == []
        assert data["upcoming_assignments"] == []
        assert data["subjects"] == []

    def test_dashboard_with_data(self, client, auth_headers, test_subject,
                                   test_study_session, test_sleep_log,
                                   test_assignment):
        r = client.get("/api/dashboard/summary", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()

        # Study session exists
        assert len(data["study_hours_by_date"]) >= 1
        assert len(data["study_hours_matrix"]) >= 1

        # Subject included
        assert len(data["subjects"]) == 1
        assert data["subjects"][0]["subject_name"] == "Toán cao cấp"

        # Assignment included (deadline within 30 days)
        assert len(data["upcoming_assignments"]) == 1

        # Sleep data
        assert len(data["sleep_hours_recent"]) == 1
        assert data["sleep_hours_recent"][0] == 8.0

    def test_dashboard_isolated_between_users(self, client, auth_headers,
                                                second_auth_headers, test_subject,
                                                second_subject):
        r1 = client.get("/api/dashboard/summary", headers=auth_headers)
        assert len(r1.json()["subjects"]) == 1
        assert r1.json()["subjects"][0]["subject_name"] == "Toán cao cấp"

        r2 = client.get("/api/dashboard/summary", headers=second_auth_headers)
        assert len(r2.json()["subjects"]) == 1
        assert r2.json()["subjects"][0]["subject_name"] == "Vật lý"
