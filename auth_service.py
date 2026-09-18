from sqlalchemy.orm import Session

from models.user import User
from repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
)
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from utils.enums import UserRole
from utils.exceptions import bad_request, not_found, unauthorized
from utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


def register_user(
    db: Session,
    payload: RegisterRequest,
) -> User:

    existing_user = get_user_by_email(
        db,
        payload.email,
    )

    if existing_user:
        raise bad_request(
            "Email is already registered"
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        hashed_password=hash_password(
            payload.password
        ),
        role=payload.role,
        is_active=True,
    )

    return create_user(db, user)


def authenticate_user(
    db: Session,
    payload: LoginRequest,
) -> User:

    user = get_user_by_email(
        db,
        payload.email,
    )

    if not user:
        raise unauthorized(
            "Invalid email or password"
        )

    if not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise unauthorized(
            "Invalid email or password"
        )

    if not user.is_active:
        raise unauthorized(
            "User account is inactive"
        )

    return user


def login_user(
    db: Session,
    payload: LoginRequest,
) -> dict:

    user = authenticate_user(
        db,
        payload,
    )

    return {
        "access_token": create_access_token(
            user.id
        ),
        "refresh_token": create_refresh_token(
            user.id
        ),
        "token_type": "bearer",
    }


def get_user(
    db: Session,
    user_id: int,
) -> User:

    user = get_user_by_id(
        db,
        user_id,
    )

    if not user:
        raise not_found("User not found")

    return user


def refresh_user_token(
    db: Session,
    user_id: int,
) -> dict:

    user = get_user(db, user_id)

    if not user.is_active:
        raise unauthorized(
            "User account is inactive"
        )

    return {
        "access_token": create_access_token(
            user.id
        ),
        "refresh_token": create_refresh_token(
            user.id
        ),
        "token_type": "bearer",
    }


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:

    if not verify_password(
        current_password,
        user.hashed_password,
    ):
        raise bad_request(
            "Current password is incorrect"
        )

    if current_password == new_password:
        raise bad_request(
            "New password must be different from current password"
        )

    user.hashed_password = hash_password(
        new_password
    )

    update_user(db, user)