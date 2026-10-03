"""
Middleware y gestor en memoria de limitación de tasa (Rate Limiting) - F-40.

Implementa control de frecuencia mediante ventana deslizante (Sliding Window Log)
focalizado exclusivamente en endpoints de autenticación (POST /api/auth/login y
POST /api/auth/register), con política de desalojo LRU para prevención de agotamiento
de memoria (OOM).
"""

from __future__ import annotations

import os
import time
from collections import OrderedDict
from threading import Lock
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.responses import JSONResponse


class InMemoryRateLimiter:
    """
    Limitador de tasa por ventana deslizante thread-safe con mitigación de fugas de memoria.
    
    Almacena timestamps por IP en un OrderedDict. Aplica purga pasiva de marcas
    expiradas y desalojo amortizado (hasta el 90% de capacidad) al superar max_keys.
    """

    def __init__(self, limit: int = 10, window_seconds: int = 60, max_keys: int = 10000) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._records: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = Lock()

    def is_rate_limited(self, key: str, now: float | None = None) -> tuple[bool, int]:
        """
        Evalúa si la clave excede el límite permitido en la ventana.
        Retorna (is_limited: bool, retry_after: int).
        """
        current_time = now if now is not None else time.time()
        cutoff = current_time - self.window_seconds

        with self._lock:
            timestamps = self._records.get(key, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= self.limit:
                oldest_timestamp = valid_timestamps[0]
                retry_after = max(1, int(oldest_timestamp + self.window_seconds - current_time) + 1)
                self._records[key] = valid_timestamps
                self._records.move_to_end(key)
                return True, retry_after

            valid_timestamps.append(current_time)
            self._records[key] = valid_timestamps
            self._records.move_to_end(key)

            if len(self._records) > self.max_keys:
                self._cleanup_memory(cutoff)

            return False, 0

    def _cleanup_memory(self, cutoff: float) -> None:
        """Purga claves con marcas expiradas y desaloja las más antiguas hasta el 90% de capacidad."""
        to_delete = [
            k for k, timestamps in self._records.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for k in to_delete:
            del self._records[k]

        target_size = int(self.max_keys * 0.9)
        while len(self._records) > target_size:
            self._records.popitem(last=False)

    def reset(self) -> None:
        """Reinicia el almacén en memoria."""
        with self._lock:
            self._records.clear()


# Instancia singleton predeterminada
default_rate_limiter = InMemoryRateLimiter(limit=10, window_seconds=60, max_keys=10000)


class RateLimitMiddleware:
    """Middleware ASGI para throttling en endpoints sensibles de autenticación."""

    PROTECTED_PATHS = {
        "/api/auth/login",
        "/api/auth/register",
    }

    def __init__(self, app: ASGIApp, limiter: InMemoryRateLimiter | None = None) -> None:
        self.app = app
        self.limiter = limiter or default_rate_limiter

    def _is_enabled(self) -> bool:
        # Precedencia: 1) FORCE_RATE_LIMIT=1, 2) TESTING=1 -> False, 3) RATE_LIMIT_ENABLED
        if os.getenv("FORCE_RATE_LIMIT") == "1":
            return True
        if os.getenv("TESTING") == "1":
            return False
        return os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")

    def _get_client_ip(self, scope: Scope) -> str:
        headers = dict(scope.get("headers", []))
        x_forwarded_for = headers.get(b"x-forwarded-for")
        if x_forwarded_for:
            ip_str = x_forwarded_for.decode("latin1").split(",")[0].strip()
            if ip_str:
                return ip_str
        client = scope.get("client")
        return client[0] if client else "127.0.0.1"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] == "POST":
            path = scope.get("path", "").rstrip("/")
            if path in self.PROTECTED_PATHS and self._is_enabled():
                client_ip = self._get_client_ip(scope)
                is_limited, retry_after = self.limiter.is_rate_limited(client_ip)
                if is_limited:
                    response = JSONResponse(
                        status_code=429,
                        headers={"Retry-After": str(retry_after)},
                        content={
                            "detail": "Demasiados intentos de autenticación. Por favor, inténtelo de nuevo más tarde.",
                            "retry_after": retry_after,
                        },
                    )
                    await response(scope, receive, send)
                    return

        await self.app(scope, receive, send)
