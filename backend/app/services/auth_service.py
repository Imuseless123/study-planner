from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
)
from app.models.orm_models import User
from app.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, username: str, password: str, email: str) -> User:
        if self.repo.get_by_username(username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
        if self.repo.get_by_email(email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        return self.repo.create(username, email, hash_password(password))

    def login(self, username: str, password: str) -> tuple[str, str, User]:
        user = self.repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        return (
            create_access_token(str(user.user_id)),
            create_refresh_token(str(user.user_id)),
            user,
        )
