from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Downstream
    RISK_API_URL: str = "http://localhost:8001"
    LP_SOLVER_API_URL: str = "http://localhost:8002"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Consent
    CONSENT_VERSION: str = "1.0"
    CONSENT_DURATION_DAYS: int = 365


@lru_cache
def get_settings() -> Settings:
    return Settings()