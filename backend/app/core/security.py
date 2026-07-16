"""Password, JWT, and provider-token cryptography."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from cryptography.fernet import Fernet, InvalidToken
from pwdlib import PasswordHash

from app.core.config import Settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password with the current recommended Argon2 parameters."""

    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification delegated to pwdlib."""

    return password_hash.verify(password, encoded)


def create_access_token(user_id: UUID, settings: Settings) -> str:
    """Create a short-lived signed bearer token for one user."""

    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> UUID:
    """Validate a bearer token and return its user identifier."""

    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if payload.get("type") != "access" or not payload.get("sub"):
        raise jwt.InvalidTokenError("Invalid token type")
    return UUID(payload["sub"])


class TokenCipher:
    """Encrypt Meta access tokens before database persistence."""

    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, token: str) -> str:
        return self._fernet.encrypt(token.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt provider token") from exc
