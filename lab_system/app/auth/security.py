import base64
import hashlib
import hmac
import importlib.util
import secrets

_BCRYPT_SPEC = importlib.util.find_spec("bcrypt")
if _BCRYPT_SPEC is not None:
    import bcrypt
else:
    bcrypt = None

_PBKDF2_PREFIX = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 260_000


def _hash_password_pbkdf2(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        _PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode().rstrip("=")
    digest_b64 = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return f"{_PBKDF2_PREFIX}${_PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"


def _verify_password_pbkdf2(password: str, password_hash: str) -> bool:
    try:
        prefix, iterations_raw, salt_b64, digest_b64 = password_hash.split("$", 3)
        if prefix != _PBKDF2_PREFIX:
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_b64 + "=" * (-len(salt_b64) % 4))
        expected = base64.urlsafe_b64decode(
            digest_b64 + "=" * (-len(digest_b64) % 4)
        )
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(actual, expected)


def hash_password(password: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return _hash_password_pbkdf2(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(_PBKDF2_PREFIX):
        return _verify_password_pbkdf2(password, password_hash)
    if bcrypt is not None:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    return False
