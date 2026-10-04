from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.api.deps import get_current_user
from app.models.orm_models import User, Consent
from app.schemas.consent import ConsentCreate, ConsentResponse

router = APIRouter(prefix="/api/consent", tags=["consent"])
settings = get_settings()


@router.post("", response_model=ConsentResponse)
def sign_consent(
    req: ConsentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = Consent(
        user_id=user.user_id,
        version=req.version,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.CONSENT_DURATION_DAYS),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return ConsentResponse(
        consent_id=str(c.consent_id),
        version=c.version,
        signed_at=c.signed_at,
        expires_at=c.expires_at,
        withdrawn_at=c.withdrawn_at,
    )


@router.get("", response_model=ConsentResponse | None)
def get_consent(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = (
        db.query(Consent)
        .filter(Consent.user_id == user.user_id, Consent.withdrawn_at.is_(None))
        .order_by(Consent.signed_at.desc())
        .first()
    )
    if not c:
        return None
    return ConsentResponse(
        consent_id=str(c.consent_id),
        version=c.version,
        signed_at=c.signed_at,
        expires_at=c.expires_at,
        withdrawn_at=c.withdrawn_at,
    )


@router.post("/withdraw")
def withdraw(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = (
        db.query(Consent)
        .filter(Consent.user_id == user.user_id, Consent.withdrawn_at.is_(None))
        .first()
    )
    if c:
        c.withdrawn_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "ok"}
