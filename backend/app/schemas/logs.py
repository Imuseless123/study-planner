from datetime import datetime, date
from pydantic import BaseModel, Field


# ====== Requests ======

class StudyLogRequest(BaseModel):
    subject_id: str
    start_time: datetime
    duration: float = Field(gt=0, le=12)
    focus_level: int = Field(ge=1, le=5)


class SleepLogRequest(BaseModel):
    sleep_time: datetime
    wake_time: datetime
    quality: int = Field(ge=1, le=5)


class MoodLogRequest(BaseModel):
    log_date: date
    energy_level: int = Field(ge=1, le=5)
    stress_level: int = Field(ge=1, le=5)


# ====== Responses ======

class StudyLogResponse(BaseModel):
    status: str
    session_id: str


class SleepLogResponse(BaseModel):
    status: str
    sleep_id: str


class MoodLogResponse(BaseModel):
    status: str
    mood_id: str


# ====== List items ======

class StudyLogItem(BaseModel):
    session_id: str
    subject_id: str
    subject_name: str
    start_time: datetime
    duration: float
    focus_level: int


class SleepLogItem(BaseModel):
    sleep_id: str
    sleep_time: datetime
    wake_time: datetime
    quality: int
    hours: float  # derived


class MoodLogItem(BaseModel):
    mood_id: str
    log_date: date
    energy_level: int
    stress_level: int


class StudyLogListResponse(BaseModel):
    items: list[StudyLogItem]
    total: int


class SleepLogListResponse(BaseModel):
    items: list[SleepLogItem]
    total: int


class MoodLogListResponse(BaseModel):
    items: list[MoodLogItem]
    total: int
