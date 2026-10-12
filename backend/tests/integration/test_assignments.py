"""Integration tests for /api/assignments."""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.mark.integration
class TestAssignmentsCRUD:
    def test_list_empty(self, client, auth_headers):
        r = client.get("/api/assignments", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["assignments"] == []

    def test_create_assignment(self, client, auth_headers, test_subject):
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        r = client.post("/api/assignments", json={
            "subject_id": str(test_subject.subject_id),
            "title": "HW 1",
            "deadline": deadline,
            "required_hours": 4.0,
            "priority": 5,
        }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "HW 1"
        assert data["subject_name"] == "Toán cao cấp"
        assert data["days_until_deadline"] >= 6
        assert data["is_overdue"] is False

    def test_create_assignment_deadline_in_past(self, client, auth_headers,
                                                 test_subject):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        r = client.post("/api/assignments", json={
            "subject_id": str(test_subject.subject_id),
            "title": "Late HW",
            "deadline": past,
            "required_hours": 4.0,
            "priority": 5,
        }, headers=auth_headers)
        assert r.status_code == 422

    def test_list_has_subject_name(self, client, auth_headers, test_assignment):
        r = client.get("/api/assignments", headers=auth_headers)
        assert r.status_code == 200
        items = r.json()["assignments"]
        assert len(items) >= 1
        assert items[0]["subject_name"] == "Toán cao cấp"

    def test_stats_endpoint(self, client, auth_headers, test_assignment):
        r = client.get("/api/assignments/stats", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["overdue"] == 0
        assert data["high_priority"] == 1
        assert data["total_required_hours"] == 4.0

    def test_update_assignment_partial(self, client, auth_headers, test_assignment):
        r = client.put(
            f"/api/assignments/{test_assignment.assignment_id}",
            json={"priority": 3},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["priority"] == 3
        assert data["title"] == "Bài tập chương 1"  # unchanged

    def test_delete_assignment(self, client, auth_headers, test_assignment):
        r = client.delete(
            f"/api/assignments/{test_assignment.assignment_id}",
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_user_isolation(self, client, auth_headers, second_auth_headers,
                             test_assignment):
        # User B cannot see User A's assignments
        r = client.get("/api/assignments", headers=second_auth_headers)
        assert r.json()["assignments"] == []
