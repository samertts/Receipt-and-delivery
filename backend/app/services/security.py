from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.rbac import permissions_for_role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.effective_secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        return {}
    if payload.get("type") != "access" or not payload.get("sub"):
        return {}
    return payload


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    sub: str, role: str = "user", expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    exp = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": sub,
        "role": role,
        "permissions": permissions_for_role(role),
        "exp": exp,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(
        payload, settings.effective_secret_key, algorithm=settings.algorithm
    )


def create_refresh_token(sub: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": sub,
        "exp": exp,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(
        payload, settings.effective_secret_key, algorithm=settings.algorithm
    )
