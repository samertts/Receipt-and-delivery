import os

os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ALLOWED_ORIGINS"] = "http://testserver"
os.environ["LOG_LEVEL"] = "CRITICAL"

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import Base
from app.db.session import get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c


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
    return response.json()["access_token"]


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
    return response.json()["access_token"]
