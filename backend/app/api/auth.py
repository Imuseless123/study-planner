from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.api.deps import get_current_user
from app.models.orm_models import User
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse, UserMeResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService(db).register(req.username, req.password, req.email)
    return RegisterResponse(status="ok", user_id=str(user.user_id))


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    access, refresh, _ = AuthService(db).login(req.username, req.password)
    response.set_cookie(
        key="refresh_token", value=refresh,
        httponly=True, secure=False, samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    return LoginResponse(status="ok", token=access, refresh_token=refresh)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"status": "ok"}


@router.get("/me", response_model=UserMeResponse)
def me(user: User = Depends(get_current_user)):
    return UserMeResponse(
        user_id=str(user.user_id),
        username=user.username,
        email=user.email,
        created_at=user.created_at,
    )
