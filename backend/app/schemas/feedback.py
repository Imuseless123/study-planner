from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    schedule_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    feedback_id: str
    schedule_id: str
    rating: int
    comment: str | None
    created_at: datetime
