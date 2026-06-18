import os

os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ALLOWED_ORIGINS"] = "http://testserver"
os.environ["LOG_LEVEL"] = "CRITICAL"

from typing import Generator

import pytest
from app.db import base  # noqa: F401 - register models with Base before metadata operations
from app.db.session import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine_local = None
_session_factory_local = None
_connection_local = None


def _get_engine():
    global _engine_local
    if _engine_local is None:
        _engine_local = create_engine(
            "sqlite:///./test.db",
            connect_args={"check_same_thread": False},
        )
    return _engine_local


def _get_connection():
    global _connection_local
    if _connection_local is None:
        _connection_local = _get_engine().connect()
    return _connection_local


def _get_session_factory():
    global _session_factory_local
    if _session_factory_local is None:
        _session_factory_local = sessionmaker(
            bind=_get_engine(), autoflush=False, autocommit=False,
        )
    return _session_factory_local


def override_get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    from app.core.container import reset_container
    reset_container()
    connection = _get_connection()
    Base.metadata.create_all(bind=connection)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=connection)
        reset_container()


@pytest.fixture
def db() -> Generator:
    session = _get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c


def _extract_token(body: dict) -> str:
    if "data" in body and isinstance(body["data"], dict) and "access_token" in body["data"]:
        return body["data"]["access_token"]
    return body.get("access_token", "")


@pytest.fixture
def admin_token(client, db: Session) -> str:
    from app.models.user import User
    from app.services.security import hash_password

    user = User(
        username="admin",
        full_name="Admin User",
        password_hash=hash_password("Admin@123"),
        role="admin",
        status="active",
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@123"},
    )
    body = response.json()
    return _extract_token(body)


@pytest.fixture
def user_token(client, db: Session) -> str:
    from app.models.user import User
    from app.services.security import hash_password

    user = User(
        username="user1",
        full_name="Regular User",
        password_hash=hash_password("User@1234"),
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "User@1234"},
    )
    body = response.json()
    return _extract_token(body)
