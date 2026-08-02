"""Adaptadores de autenticación — implementaciones de PasswordHasherPort y TokenServicePort."""
from __future__ import annotations
import datetime
import bcrypt
import jwt
from backend.domain.ports import PasswordHasherPort, TokenServicePort


class BcryptPasswordHasherAdapter(PasswordHasherPort):
    def hash(self, plain_password: str) -> str:
        return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


class JWTTokenServiceAdapter(TokenServicePort):
    def __init__(self, secret_key: str = "dev-secret-key-change-in-production",
                 access_ttl_minutes: int = 15, refresh_ttl_days: int = 7) -> None:
        self._secret_key = secret_key
        self._access_ttl = datetime.timedelta(minutes=access_ttl_minutes)
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

    def verify_token(self, token: str) -> str | None:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload.get("sub")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
