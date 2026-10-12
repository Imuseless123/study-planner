"""Integration tests for /api/consent."""
import pytest


@pytest.mark.integration
class TestConsent:
    def test_sign_consent(self, client, test_user, auth_headers):
        r = client.post(
            "/api/consent",
            json={"version": "1.0"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "1.0"
        assert data["withdrawn_at"] is None

    def test_get_consent_before_signing_returns_null(self, client, test_user, auth_headers):
        r = client.get("/api/consent", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() is None

    def test_get_consent_after_signing(self, client, test_user, auth_headers,
                                        test_consent):
        r = client.get("/api/consent", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["version"] == "1.0"

    def test_withdraw_consent(self, client, test_user, auth_headers, test_consent):
        r = client.post("/api/consent/withdraw", headers=auth_headers)
        assert r.status_code == 200

        r2 = client.get("/api/consent", headers=auth_headers)
        # Sau khi withdraw, GET returns None (vì filter withdrawn_at IS NULL)
        assert r2.json() is None

    def test_consent_requires_auth(self, client):
        r = client.post("/api/consent", json={"version": "1.0"})
        assert r.status_code in (401, 403)
