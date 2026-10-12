from datetime import datetime
from pydantic import BaseModel


class DataExportResponse(BaseModel):
    """Response cho GET /api/user/data."""
    exported_at: datetime
    schema_version: str
    user: dict
    subjects: list[dict]
    assignments: list[dict]
    study_sessions: list[dict]
    sleep_logs: list[dict]
    mood_logs: list[dict]
    schedules: list[dict]
    feedback: list[dict]
    consents: list[dict]
    stats: dict


class DeleteAccountRequest(BaseModel):
    """Body cho DELETE /api/user/data — yêu cầu confirm rõ ràng."""
    confirm: bool
    username_confirmation: str  # User phải gõ đúng username để confirm
