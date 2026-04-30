from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.users import UserRepository

DbSession = Annotated[Session, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Missing token subject")
        user_id = int(subject)
    except (ValueError, TypeError):
        raise UnauthorizedError("Invalid authentication credentials.")

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Invalid authentication credentials.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
