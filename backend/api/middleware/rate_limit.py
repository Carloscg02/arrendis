"""
Middleware y gestor en memoria de limitación de tasa estratificada (Tiered Rate Limiting) - F-40.

Implementa control de frecuencia mediante ventana deslizante (Sliding Window Log)
en tres niveles de protección:
1. Nivel Auth (10 req/min): POST /api/auth/login y POST /api/auth/register (anti-fuerza bruta).
2. Nivel Cómputo Pesado (30 req/min): generación de PDFs, tasación IA y subida de facturas.
3. Nivel Global API (100 req/min): resto de rutas /api/* para tráfico y navegación legítima.

Incluye política de desalojo LRU para prevención estricta de agotamiento de memoria (OOM).
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


class TieredRateLimiterGroup:
    """Agrupador de limitadores estratificados que permite resetearlos de forma unificada."""

    def __init__(self, auth: InMemoryRateLimiter, heavy: InMemoryRateLimiter, global_: InMemoryRateLimiter) -> None:
        self.auth = auth
        self.heavy = heavy
        self.global_ = global_

    def reset(self) -> None:
        self.auth.reset()
        self.heavy.reset()
        self.global_.reset()

    def is_rate_limited(self, key: str, now: float | None = None) -> tuple[bool, int]:
        return self.auth.is_rate_limited(key, now)

    @property
    def limit(self) -> int:
        return self.auth.limit

    @property
    def window_seconds(self) -> int:
        return self.auth.window_seconds

    @property
    def max_keys(self) -> int:
        return self.auth.max_keys


# Instancias predeterminadas por nivel
default_auth_limiter = InMemoryRateLimiter(limit=10, window_seconds=60, max_keys=10000)
default_heavy_limiter = InMemoryRateLimiter(limit=30, window_seconds=60, max_keys=10000)
default_global_limiter = InMemoryRateLimiter(limit=100, window_seconds=60, max_keys=10000)

default_rate_limiter = TieredRateLimiterGroup(
    default_auth_limiter,
    default_heavy_limiter,
    default_global_limiter,
)


class RateLimitMiddleware:
    """Middleware ASGI para throttling estratificado en toda la API."""

    AUTH_PATHS = {
        "/api/auth/login",
        "/api/auth/register",
    }

    HEAVY_PATH_SUFFIXES = (
        "/valuation",
        "/fiscal-report",
        "/fiscal-report/pdf",
        "/upload",
        "/upload-multiple",
    )

    EXEMPT_PREFIXES = (
        "/api/images",
    )

    def __init__(
        self,
        app: ASGIApp,
        auth_limiter: InMemoryRateLimiter | None = None,
        heavy_limiter: InMemoryRateLimiter | None = None,
        global_limiter: InMemoryRateLimiter | None = None,
        limiter: InMemoryRateLimiter | TieredRateLimiterGroup | None = None,
    ) -> None:
        self.app = app
        if isinstance(limiter, TieredRateLimiterGroup):
            self.auth_limiter = limiter.auth
            self.heavy_limiter = limiter.heavy
            self.global_limiter = limiter.global_
        elif isinstance(limiter, InMemoryRateLimiter):
            self.auth_limiter = limiter
            self.heavy_limiter = heavy_limiter or default_heavy_limiter
            self.global_limiter = global_limiter or default_global_limiter
        else:
            self.auth_limiter = auth_limiter or default_auth_limiter
            self.heavy_limiter = heavy_limiter or default_heavy_limiter
            self.global_limiter = global_limiter or default_global_limiter

        # Alias para compatibilidad con tests existentes
        self.limiter = self.auth_limiter

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
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Peticiones preflight OPTIONS de CORS están universalmente exentas
        if scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "").rstrip("/")

        # Solo aplicamos rate limiting a rutas /api
        if not path.startswith("/api"):
            await self.app(scope, receive, send)
            return

        # Rutas estáticas de bajo coste exentas (ej: /api/images)
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            await self.app(scope, receive, send)
            return

        if not self._is_enabled():
            await self.app(scope, receive, send)
            return

        client_ip = self._get_client_ip(scope)

        # Nivel 1: Autenticación (10 req/min)
        if path in self.AUTH_PATHS and scope["method"] == "POST":
            is_limited, retry_after = self.auth_limiter.is_rate_limited(client_ip)
            if is_limited:
                response = JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    content={
                        "detail": "Demasiados intentos de autenticación. Por favor, inténtelo de nuevo más tarde.",
                        "retry_after": retry_after,
                        "tier": "auth",
                    },
                )
                await response(scope, receive, send)
                return

        # Nivel 2: Cómputo Pesado / IA (30 req/min)
        elif any(path.endswith(suffix) for suffix in self.HEAVY_PATH_SUFFIXES):
            is_limited, retry_after = self.heavy_limiter.is_rate_limited(client_ip)
            if is_limited:
                response = JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    content={
                        "detail": "Demasiadas peticiones a operaciones de alto coste. Por favor, espere antes de reintentar.",
                        "retry_after": retry_after,
                        "tier": "heavy",
                    },
                )
                await response(scope, receive, send)
                return

        # Nivel 3: Navegación General de API (100 req/min)
        else:
            is_limited, retry_after = self.global_limiter.is_rate_limited(client_ip)
            if is_limited:
                response = JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    content={
                        "detail": "Límite global de peticiones de API excedido. Por favor, espere unos momentos.",
                        "retry_after": retry_after,
                        "tier": "global",
                    },
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
