from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from utils.enums import UserRole
from utils.exceptions import forbidden, unauthorized
from utils.security import decode_token


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    token = credentials.credentials

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise unauthorized("Invalid access token")

        subject = payload.get("sub")

        if not subject:
            raise unauthorized("Invalid access token")

        user_id = int(subject)

    except (JWTError, ValueError, TypeError):
        raise unauthorized("Invalid or expired token")

    user = db.get(User, user_id)

    if not user:
        raise unauthorized("User not found")

    if not user.is_active:
        raise unauthorized("User account is inactive")

    return user


def require_roles(*roles: UserRole):

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in roles:
            raise forbidden(
                "You do not have permission to perform this action"
            )

        return current_user

    return role_checker