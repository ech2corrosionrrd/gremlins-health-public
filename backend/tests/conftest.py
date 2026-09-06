"""
Shared test fixtures.

The database URL is set before app.* is imported so the suite never touches
the developer's real gremlins_health.db.
"""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "development")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gremlins.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-used-anywhere-else-0123456789"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:TEST_BOT_TOKEN_FOR_HMAC"
os.environ["REDIS_URL"] = ""  # force the in-process limiter; no Redis in CI
os.environ["BACKEND_CORS_ORIGINS"] = "http://localhost:5173"

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402

TEST_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


def make_init_data(
    user_id: int = 555001,
    username: str = "trail_runner",
    bot_token: str = TEST_BOT_TOKEN,
    auth_date: int | None = None,
    valid_hash: bool = True,
) -> str:
    """
    Builds a Telegram initData string, correctly signed by default.

    Set valid_hash=False or pass a different bot_token to produce the exact
    payload an attacker could construct without knowing the real token.
    """
    fields = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(
            {"id": user_id, "first_name": "Trail", "username": username},
            separators=(",", ":"),
        ),
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    fields["hash"] = digest if valid_hash else "0" * 64
    return urlencode(fields)


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    """A fresh schema per test keeps ordering out of the assertions."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await limiter.reset()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    """Registers a user and returns ready-to-use Authorization headers."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "hiker_pro",
            "email": "hiker@gremlins.health",
            "password": "StrongPassword2026!",
        },
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def anyio_backend():
    return "asyncio"
