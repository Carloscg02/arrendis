"""Adaptadores de autenticación — implementaciones de PasswordHasherPort y TokenServicePort."""
from __future__ import annotations
import os
import datetime
import bcrypt
import jwt
from backend.domain.ports import PasswordHasherPort, TokenServicePort


class BcryptPasswordHasherAdapter(PasswordHasherPort):
    def hash(self, plain_password: str) -> str:
        return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


DEFAULT_JWT_DEV_SECRET = "dev-secret-key-change-in-production"


class JWTTokenServiceAdapter(TokenServicePort):
    def __init__(self, secret_key: str | None = None,
                 access_ttl_minutes: int | None = None, refresh_ttl_days: int = 7) -> None:
        key = secret_key if secret_key is not None else (os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY"))
        self._secret_key = key or DEFAULT_JWT_DEV_SECRET
        ttl_minutes = access_ttl_minutes if access_ttl_minutes is not None else int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self._access_ttl = datetime.timedelta(minutes=ttl_minutes)
        self._refresh_ttl = datetime.timedelta(days=refresh_ttl_days)
        self._algorithm = "HS256"

    def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": datetime.datetime.now(datetime.timezone.utc) + self._access_ttl,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.datetime.now(datetime.timezone.utc) + self._refresh_ttl,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str, expected_type: str = "access") -> str | None:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            if expected_type and payload.get("type") != expected_type:
                return None
            return payload.get("sub")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
