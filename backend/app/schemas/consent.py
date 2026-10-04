from datetime import datetime
from pydantic import BaseModel


class ConsentCreate(BaseModel):
    version: str


class ConsentResponse(BaseModel):
    consent_id: str
    version: str
    signed_at: datetime
    expires_at: datetime
    withdrawn_at: datetime | None
