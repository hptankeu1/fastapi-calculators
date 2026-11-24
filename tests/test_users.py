"""Integration tests for /users/register and /users/login."""
import pytest
from sqlalchemy import select

from app.models import User
from app.security import verify_password
from tests.conftest import register


def test_register_creates_user_and_hashes_password(client, db_session):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in body and "password_hash" not in body

    # Verify the row in the database
    user = db_session.scalar(select(User).where(User.username == "alice"))
    assert user is not None
    assert user.password_hash != "Secret123"
    assert user.password_hash.startswith("$2")  # bcrypt
    assert verify_password("Secret123", user.password_hash)


def test_register_duplicate_username_returns_409(client):
    register(client)
    r = register(client, email="other@example.com")
    assert r.status_code == 409


def test_register_duplicate_email_returns_409(client):
    register(client)
    r = register(client, username="alice2")
    assert r.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "al", "email": "a@example.com", "password": "Secret123"},       # too short
        {"username": "alice", "email": "not-an-email", "password": "Secret123"},     # bad email
        {"username": "alice", "email": "a@example.com", "password": "short1"},       # < 8 chars
        {"username": "alice", "email": "a@example.com", "password": "nodigitshere"}, # no digit
        {"username": "bad name!", "email": "a@example.com", "password": "Secret123"},# bad chars
        {"email": "a@example.com", "password": "Secret123"},                         # missing
    ],
)
def test_register_invalid_data_returns_422(client, payload):
    assert client.post("/users/register", json=payload).status_code == 422


def test_login_with_username_returns_token(client):
    register(client)
    r = client.post("/users/login", json={"username_or_email": "alice", "password": "Secret123"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "alice"


def test_login_with_email_returns_token(client):
    register(client)
    r = client.post("/users/login",
                    json={"username_or_email": "alice@example.com", "password": "Secret123"})
    assert r.status_code == 200


def test_login_wrong_password_returns_401(client):
    register(client)
    r = client.post("/users/login", json={"username_or_email": "alice", "password": "Wrong123"})
    assert r.status_code == 401


def test_login_unknown_user_returns_401(client):
    r = client.post("/users/login", json={"username_or_email": "ghost", "password": "Secret123"})
    assert r.status_code == 401


def test_me_requires_valid_token(client, auth_headers):
    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    r = client.get("/users/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"
