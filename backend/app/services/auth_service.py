from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, UserCreate


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        existing_user = self.users.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        return self.users.create(
            email=str(payload.email),
            full_name=payload.full_name.strip(),
            hashed_password=hash_password(payload.password),
        )

    def authenticate(self, payload: LoginRequest) -> User:
        user = self.users.get_by_email(str(payload.email))
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    def create_user_token(self, user: User) -> str:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        return create_access_token(subject=str(user.id), expires_delta=expires_delta)
