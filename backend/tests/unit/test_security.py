"""Unit tests for app.core.security"""
import pytest
from datetime import timedelta

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)


@pytest.mark.unit
class TestPasswordHashing:
    def test_hash_password_returns_bcrypt(self):
        h = hash_password("my_password")
        assert h.startswith("$2b$12$")
        assert len(h) == 60

    def test_verify_password_correct(self):
        h = hash_password("secret123")
        assert verify_password("secret123", h) is True

    def test_verify_password_wrong(self):
        h = hash_password("secret123")
        assert verify_password("wrong_password", h) is False

    def test_hash_is_not_deterministic(self):
        """Bcrypt uses random salt, so same password → different hash."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_long_password(self):
        """Bcrypt handles up to 72 bytes."""
        h = hash_password("a" * 100)
        assert verify_password("a" * 100, h) is True


@pytest.mark.unit
class TestJWT:
    def test_create_access_token(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_token_success(self):
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        token = create_refresh_token("user-123")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("invalid.token.here")

    def test_access_token_expiry(self):
        """Token with negative expiry should raise."""
        from jose import jwt, JWTError
        from app.core.config import get_settings

        settings = get_settings()
        # Tạo token đã hết hạn
        import time
        payload = {
            "sub": "user-123",
            "exp": int(time.time()) - 3600,  # 1 giờ trước
            "type": "access",
        }
        expired = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        with pytest.raises(ValueError):
            decode_token(expired)
