import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "event_conference_management_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def register_user(
    role="Attendee",
    email=None,
):
    email = email or unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "phone": "9876543210",
            "password": "Test@12345",
            "role": role,
        },
    )

    return response, email


def login_user(email, password="Test@12345"):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_attendee():
    response, _ = register_user("Attendee")

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"].startswith("Test")
    assert data["role"] == "Attendee"
    assert data["is_active"] is True
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_all_roles():
    roles = [
        "Admin",
        "Event Organizer",
        "Speaker",
        "Staff",
        "Attendee",
    ]

    for role in roles:
        response, _ = register_user(role)

        assert response.status_code == 201
        assert response.json()["role"] == role


def test_duplicate_email():
    email = unique_email()

    first, _ = register_user(
        "Attendee",
        email,
    )

    second, _ = register_user(
        "Attendee",
        email,
    )

    assert first.status_code == 201
    assert second.status_code == 400
    assert "already registered" in second.json()["detail"].lower()


def test_login_success():
    _, email = register_user("Attendee")

    response = login_user(email)

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    _, email = register_user("Attendee")

    response = login_user(
        email,
        "WrongPassword@123",
    )

    assert response.status_code == 401


def test_login_unknown_email():
    response = login_user(
        unique_email(),
    )

    assert response.status_code == 401


def test_me_requires_authentication():
    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_get_current_user():
    _, email = register_user("Attendee")

    login_response = login_user(email)

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == email


def test_invalid_access_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_refresh_token():
    _, email = register_user("Attendee")

    login_response = login_user(email)

    refresh_token = login_response.json()[
        "refresh_token"
    ]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_invalid_refresh_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-token"
        },
    )

    assert response.status_code == 401


def test_change_password():
    _, email = register_user("Attendee")

    login_response = login_user(email)

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "current_password": "Test@12345",
            "new_password": "NewTest@12345",
        },
    )

    assert response.status_code == 200

    old_login = login_user(
        email,
        "Test@12345",
    )

    assert old_login.status_code == 401

    new_login = login_user(
        email,
        "NewTest@12345",
    )

    assert new_login.status_code == 200


def test_wrong_current_password():
    _, email = register_user("Attendee")

    login_response = login_user(email)

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "current_password": "WrongPassword@123",
            "new_password": "NewTest@12345",
        },
    )

    assert response.status_code == 400


def test_admin_can_deactivate_user():
    _, admin_email = register_user("Admin")

    _, user_email = register_user("Attendee")

    admin_login = login_user(admin_email)

    admin_token = admin_login.json()["access_token"]

    db = SessionLocal()

    try:
        result = db.execute(
            text(
                "SELECT id FROM users WHERE email = :email"
            ),
            {"email": user_email},
        )

        user_id = result.scalar_one()
    finally:
        db.close()

    response = client.patch(
        f"/api/v1/auth/users/{user_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        params={
            "is_active": False
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivated_user_cannot_login():
    _, email = register_user("Attendee")

    db = SessionLocal()

    try:
        result = db.execute(
            text(
                "SELECT id FROM users WHERE email = :email"
            ),
            {"email": email},
        )

        user_id = result.scalar_one()

        db.execute(
            text(
                "UPDATE users "
                "SET is_active = false "
                "WHERE id = :id"
            ),
            {"id": user_id},
        )

        db.commit()
    finally:
        db.close()

    response = login_user(email)

    assert response.status_code == 401