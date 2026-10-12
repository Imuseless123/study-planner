"""Integration tests for /api/auth endpoints."""
import pytest


@pytest.mark.integration
class TestRegister:
    def test_register_success(self, client):
        r = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "password123",
            "email": "new@example.com",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "user_id" in data

    def test_register_duplicate_username(self, client, test_user):
        r = client.post("/api/auth/register", json={
            "username": "test_user",  # already exists
            "password": "password123",
            "email": "different@example.com",
        })
        assert r.status_code == 409
        assert "Username already exists" in r.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        r = client.post("/api/auth/register", json={
            "username": "different_user",
            "password": "password123",
            "email": "test@example.com",  # already exists
        })
        assert r.status_code == 409

    def test_register_invalid_username(self, client):
        r = client.post("/api/auth/register", json={
            "username": "ab",  # too short
            "password": "password123",
            "email": "x@example.com",
        })
        assert r.status_code == 422

    def test_register_invalid_email(self, client):
        r = client.post("/api/auth/register", json={
            "username": "valid_user",
            "password": "password123",
            "email": "not-an-email",
        })
        assert r.status_code == 422


@pytest.mark.integration
class TestLogin:
    def test_login_success(self, client, test_user):
        r = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password_123",
        })
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["status"] == "ok"

    def test_login_wrong_password(self, client, test_user):
        r = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "wrong_password",
        })
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "any",
        })
        assert r.status_code == 401


@pytest.mark.integration
class TestMe:
    def test_me_with_valid_token(self, client, test_user, auth_headers):
        r = client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "test_user"
        assert data["email"] == "test@example.com"
        assert data["user_id"] == str(test_user.user_id)

    def test_me_without_token(self, client):
        r = client.get("/api/auth/me")
        # FastAPI HTTPBearer returns 403 by default
        assert r.status_code in (401, 403)

    def test_me_with_invalid_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert r.status_code == 401

    def test_me_with_refresh_token_rejected(self, client, test_user):
        """Refresh token should NOT work as access token."""
        from app.core.security import create_refresh_token
        refresh = create_refresh_token(str(test_user.user_id))
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh}"})
        assert r.status_code == 401


@pytest.mark.integration
class TestLogout:
    def test_logout_returns_ok(self, client):
        r = client.post("/api/auth/logout")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
