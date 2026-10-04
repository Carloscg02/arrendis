"""
Middleware ASGI de Cabeceras HTTP de Seguridad (F-39).

Inyecta cabeceras recomendadas por OWASP en todas las respuestas HTTP de la API,
incluyendo respuestas de error 4xx y 5xx, sin interferir con fuentes externas
(Google Fonts) ni Vite HMR en desarrollo.
"""

from __future__ import annotations

import os
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Middleware ASGI puro para inyección de cabeceras HTTP de seguridad."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
                headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "img-src 'self' data: https: blob:; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com data:; "
                    "script-src 'self' 'unsafe-inline'; "
                    "connect-src 'self' https: ws: wss:;"
                )

                env = os.getenv("ENVIRONMENT", "").lower()
                force_hsts = os.getenv("FORCE_HSTS", "") == "1"
                if env in ("production", "staging") or force_hsts:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            await send(message)

        await self.app(scope, receive, send_with_security_headers)
