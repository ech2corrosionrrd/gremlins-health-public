"""
Sliding-window rate limiting for FastAPI.

Two backends: an in-process limiter (correct for a single worker) and a Redis
limiter that is shared across workers and survives restarts. Redis is used
when reachable and the in-process one is the fallback, so a Redis outage
degrades the limit rather than removing it.
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import time
from collections import defaultdict
from typing import Optional, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

# Never rate-limited: liveness probes and the docs the limiter itself needs.
_EXEMPT_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})
# Authentication is limited far more aggressively than the rest of the API.
_AUTH_PREFIX = "/api/v1/auth"


class SlidingWindowRateLimiter:
    """Async-safe in-memory sliding window limiter (per-process)."""

    def __init__(self, cleanup_interval: float = 300.0) -> None:
        self._records: dict[str, list[float]] = defaultdict(list)
        self._windows: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.monotonic()

    async def is_allowed(
        self, key: str, max_requests: int, window_seconds: float = 60.0
    ) -> Tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds

        async with self._lock:
            self._windows[key] = window_seconds
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup_stale(now)
                self._last_cleanup = now

            valid = [t for t in self._records[key] if t > cutoff]
            self._records[key] = valid

            if len(valid) >= max_requests:
                retry_after = max(1, int(window_seconds - (now - valid[0])))
                return False, retry_after

            valid.append(now)
            return True, 0

    def _cleanup_stale(self, now: float) -> None:
        stale = [
            k
            for k, ts in self._records.items()
            if not ts or ts[-1] <= now - self._windows.get(k, 60.0)
        ]
        for k in stale:
            self._records.pop(k, None)
            self._windows.pop(k, None)

    async def reset(self) -> None:
        async with self._lock:
            self._records.clear()
            self._windows.clear()


class RedisRateLimiter:
    """
    Sliding window backed by a Redis sorted set, shared by all workers.

    Falls back to the in-process limiter whenever Redis is unavailable, so a
    broker outage cannot silently disable rate limiting.
    """

    def __init__(self, url: str, fallback: SlidingWindowRateLimiter) -> None:
        self._url = url
        self._fallback = fallback
        self._client = None
        self._unavailable_logged = False

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as aioredis

            self._client = aioredis.from_url(
                self._url, encoding="utf-8", decode_responses=True
            )
        return self._client

    async def is_allowed(
        self, key: str, max_requests: int, window_seconds: float = 60.0
    ) -> Tuple[bool, int]:
        try:
            client = await self._get_client()
            now = time.time()
            cutoff = now - window_seconds
            redis_key = f"rl:{key}"

            pipe = client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, cutoff)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {f"{now}:{id(pipe)}": now})
            pipe.expire(redis_key, int(window_seconds) + 1)
            _, count, _, _ = await pipe.execute()

            if count >= max_requests:
                # Undo our own insertion so a blocked request does not extend
                # the window it was blocked by.
                await client.zremrangebyscore(redis_key, now, now)
                oldest = await client.zrange(redis_key, 0, 0, withscores=True)
                retry_after = 1
                if oldest:
                    retry_after = max(1, int(window_seconds - (now - oldest[0][1])))
                return False, retry_after

            self._unavailable_logged = False
            return True, 0
        except Exception as exc:  # redis down, misconfigured, etc.
            if not self._unavailable_logged:
                logger.warning(
                    "Redis rate limiter unavailable (%s); using in-process limiter", exc
                )
                self._unavailable_logged = True
            self._client = None
            return await self._fallback.is_allowed(key, max_requests, window_seconds)


limiter = SlidingWindowRateLimiter()


def client_identifier(request: Request, trusted_proxy_count: int) -> str:
    """
    Resolves the caller's address.

    Behind a reverse proxy every request appears to come from 127.0.0.1, which
    collapses all users into one bucket. When TRUSTED_PROXY_COUNT is set we
    walk X-Forwarded-For from the right, skipping that many proxy-appended
    entries, and take the next value. With the count at 0 the header is
    ignored entirely - otherwise any client could spoof its own address.
    """
    if trusted_proxy_count > 0:
        forwarded = request.headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        idx = len(parts) - trusted_proxy_count
        if 0 <= idx < len(parts):
            candidate = parts[idx]
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Protects the API against high-frequency spam, scraping and credential stuffing."""

    def __init__(
        self,
        app,
        max_requests_per_minute: Optional[int] = None,
        auth_requests_per_minute: Optional[int] = None,
        limiter_instance=None,
    ) -> None:
        super().__init__(app)
        self.max_rpm = max_requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.auth_rpm = auth_requests_per_minute or settings.RATE_LIMIT_AUTH_PER_MINUTE
        if limiter_instance is not None:
            self.limiter = limiter_instance
        elif settings.REDIS_URL:
            self.limiter = RedisRateLimiter(settings.REDIS_URL, limiter)
        else:
            self.limiter = limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in _EXEMPT_PATHS or path.startswith("/assets"):
            return await call_next(request)

        client_ip = client_identifier(request, settings.TRUSTED_PROXY_COUNT)

        if path.startswith(_AUTH_PREFIX):
            key, limit = f"auth:{client_ip}", self.auth_rpm
        else:
            # Authenticated callers get their own bucket so one busy NAT does
            # not throttle everyone behind it.
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from app.core.security import decode_access_token

                user_id = decode_access_token(auth_header[7:])
                key = f"user:{user_id}" if user_id else f"ip:{client_ip}"
            else:
                key = f"ip:{client_ip}"
            limit = self.max_rpm

        allowed, retry_after = await self.limiter.is_allowed(
            key=key, max_requests=limit, window_seconds=60.0
        )

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
