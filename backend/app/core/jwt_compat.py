"""Small compatibility surface for JWT operations used by the backend.

PyJWT is used instead of python-jose so the backend does not pull the
unmaintained ecdsa/pyasn1 dependency chain into the authentication path.
"""

from __future__ import annotations

import jwt as _pyjwt
from jwt import ExpiredSignatureError, InvalidTokenError

JWTError = InvalidTokenError
jwt = _pyjwt

__all__ = ["JWTError", "ExpiredSignatureError", "jwt"]
