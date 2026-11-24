"""Shared fixtures. Tests run against the real PostgreSQL in DATABASE_URL."""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_test_db"
)

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def create_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE calculations, users RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def register(client, username="alice", email="alice@example.com", password="Secret123"):
    return client.post(
        "/users/register",
        json={"username": username, "email": email, "password": password},
    )


def login_headers(client, username="alice", password="Secret123"):
    r = client.post("/users/login", json={"username_or_email": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth_headers(client):
    assert register(client).status_code == 201
    return login_headers(client)
