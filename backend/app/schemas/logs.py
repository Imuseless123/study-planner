from datetime import datetime, date
from pydantic import BaseModel, Field


class StudyLogRequest(BaseModel):
    subject_id: str
    start_time: datetime
    duration: float = Field(gt=0, le=12)
    focus_level: int = Field(ge=1, le=5)


class StudyLogResponse(BaseModel):
    status: str
    session_id: str


class SleepLogRequest(BaseModel):
    sleep_time: datetime
    wake_time: datetime
    quality: int = Field(ge=1, le=5)


class SleepLogResponse(BaseModel):
    status: str
    sleep_id: str


class MoodLogRequest(BaseModel):
    log_date: date
    energy_level: int = Field(ge=1, le=5)
    stress_level: int = Field(ge=1, le=5)


class MoodLogResponse(BaseModel):
    status: str
    mood_id: str
