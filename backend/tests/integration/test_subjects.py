"""Integration tests for /api/subjects."""
import pytest


@pytest.mark.integration
class TestSubjectsCRUD:
    def test_list_empty(self, client, auth_headers):
        r = client.get("/api/subjects", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["subjects"] == []

    def test_create_subject(self, client, auth_headers):
        r = client.post("/api/subjects", json={
            "subject_name": "Linear Algebra",
            "difficulty": 4,
            "priority": 5,
        }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["subject_name"] == "Linear Algebra"
        assert "subject_id" in data

    def test_create_subject_invalid_difficulty(self, client, auth_headers):
        r = client.post("/api/subjects", json={
            "subject_name": "Bad",
            "difficulty": 10,
            "priority": 3,
        }, headers=auth_headers)
        assert r.status_code == 422
        assert r.json()["detail"][0]["type"] == "less_than_equal"

    def test_get_subject_by_id(self, client, auth_headers, test_subject):
        r = client.get(
            f"/api/subjects/{test_subject.subject_id}", headers=auth_headers
        )
        assert r.status_code == 200
        assert r.json()["subject_name"] == "Toán cao cấp"

    def test_update_subject_partial(self, client, auth_headers, test_subject):
        r = client.put(
            f"/api/subjects/{test_subject.subject_id}",
            json={"difficulty": 5},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["difficulty"] == 5
        assert data["subject_name"] == "Toán cao cấp"  # unchanged
        assert data["priority"] == 5  # unchanged

    def test_update_subject_empty_body(self, client, auth_headers, test_subject):
        r = client.put(
            f"/api/subjects/{test_subject.subject_id}",
            json={},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_delete_subject(self, client, auth_headers, test_subject):
        r = client.delete(
            f"/api/subjects/{test_subject.subject_id}", headers=auth_headers
        )
        assert r.status_code == 200

        # Verify gone
        r2 = client.get(
            f"/api/subjects/{test_subject.subject_id}", headers=auth_headers
        )
        assert r2.status_code == 404

    def test_user_isolation_list(self, client, auth_headers, second_auth_headers,
                                  test_subject, second_subject):
        # User A sees only his subjects
        r1 = client.get("/api/subjects", headers=auth_headers)
        assert len(r1.json()["subjects"]) == 1
        assert r1.json()["subjects"][0]["subject_name"] == "Toán cao cấp"

        # User B sees only his
        r2 = client.get("/api/subjects", headers=second_auth_headers)
        assert len(r2.json()["subjects"]) == 1
        assert r2.json()["subjects"][0]["subject_name"] == "Vật lý"

    def test_user_isolation_get(self, client, auth_headers, second_subject):
        # User A cannot GET user B's subject
        r = client.get(
            f"/api/subjects/{second_subject.subject_id}", headers=auth_headers
        )
        assert r.status_code == 404

    def test_user_isolation_delete(self, client, auth_headers, second_subject):
        r = client.delete(
            f"/api/subjects/{second_subject.subject_id}", headers=auth_headers
        )
        assert r.status_code == 404
