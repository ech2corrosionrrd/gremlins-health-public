"""
Regression tests for the authentication and economy holes found in audit.

Every test here corresponds to a bypass that was demonstrated working against
the original code. They must never go green by accident.
"""
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import make_init_data

pytestmark = pytest.mark.asyncio


def _activity_payload(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "client_activity_uuid": str(uuid.uuid4()),
        "activity_type": "hiking",
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": now.isoformat(),
        "total_steps": 12500,
        "total_distance_km": 8.5,
        "start_elevation_m": 800.0,
        "max_elevation_m": 1650.0,
        "elevation_gain_m": 850.0,
        "weather_condition": "clear",
        "temperature_c": 14.0,
        "ble_nearby_devices_count": 1,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------
# 1. The "demo user" fallback in get_current_user
# --------------------------------------------------------------------------

PROTECTED_GETS = ["/api/v1/users/me", "/api/v1/gremlins/my"]
PROTECTED_POSTS = [
    ("/api/v1/gremlins/feed", {"food_type": "energy_berry"}),
    ("/api/v1/gremlins/evolve", {}),
    ("/api/v1/users/streak/freeze", {}),
]


@pytest.mark.parametrize("path", PROTECTED_GETS)
async def test_get_without_auth_header_is_rejected(client, auth_headers, path):
    """A request with no Authorization header must not resolve to a real user."""
    resp = await client.get(path)
    assert resp.status_code in (401, 403), f"{path} leaked data: {resp.text}"


@pytest.mark.parametrize("path,body", PROTECTED_POSTS)
async def test_post_without_auth_header_is_rejected(client, auth_headers, path, body):
    resp = await client.post(path, json=body)
    assert resp.status_code in (401, 403), f"{path} accepted anonymous write"


async def test_anonymous_activity_sync_cannot_mint_currency(client, auth_headers):
    """The headline exploit: earning stamina with no credentials at all."""
    resp = await client.post("/api/v1/activities/sync", json=_activity_payload())
    assert resp.status_code in (401, 403)


async def test_garbage_and_unsigned_tokens_are_rejected(client, auth_headers):
    for token in [
        "not-a-jwt",
        "",
        # alg=none, sub=1 - forged without the signing key.
        "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0.",
    ]:
        resp = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code in (401, 403), f"accepted token {token!r}"


# --------------------------------------------------------------------------
# 2. Password-less login
# --------------------------------------------------------------------------


async def test_login_without_password_is_rejected(client, auth_headers):
    resp = await client.post(
        "/api/v1/auth/login", json={"username_or_email": "hiker@gremlins.health"}
    )
    assert resp.status_code == 401


async def test_login_with_wrong_password_is_rejected(client, auth_headers):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "hiker@gremlins.health", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_with_correct_password_succeeds(client, auth_headers):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "hiker@gremlins.health",
            "password": "StrongPassword2026!",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_registration_requires_a_password(client):
    resp = await client.post(
        "/api/v1/auth/register", json={"username": "nopass", "email": "n@example.com"}
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------
# 3. Forged Telegram initData
# --------------------------------------------------------------------------


async def test_unsigned_telegram_init_data_is_rejected(client):
    """The original code read the id straight out of the string."""
    resp = await client.post(
        "/api/v1/auth/login", json={"telegram_init_data": "id=777000"}
    )
    assert resp.status_code == 401


async def test_init_data_signed_with_wrong_token_is_rejected(client):
    forged = make_init_data(user_id=777000, bot_token="999999:ATTACKER_GUESS")
    resp = await client.post("/api/v1/auth/login", json={"telegram_init_data": forged})
    assert resp.status_code == 401


async def test_init_data_with_tampered_hash_is_rejected(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"telegram_init_data": make_init_data(valid_hash=False)},
    )
    assert resp.status_code == 401


async def test_expired_init_data_is_rejected(client):
    stale = make_init_data(auth_date=int(time.time()) - 90_000)  # >24h
    resp = await client.post("/api/v1/auth/login", json={"telegram_init_data": stale})
    assert resp.status_code == 401


async def test_valid_init_data_logs_in_and_provisions_account(client):
    resp = await client.post(
        "/api/v1/auth/login", json={"telegram_init_data": make_init_data(user_id=424242)}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["telegram_id"] == "424242"

    # Second login must reuse the account, not create a duplicate.
    again = await client.post(
        "/api/v1/auth/login", json={"telegram_init_data": make_init_data(user_id=424242)}
    )
    assert again.status_code == 200
    assert again.json()["user"]["id"] == resp.json()["user"]["id"]


async def test_telegram_only_account_cannot_be_password_logged_in(client):
    await client.post(
        "/api/v1/auth/login", json={"telegram_init_data": make_init_data(user_id=606060)}
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "trail_runner", "password": "anything"},
    )
    assert resp.status_code == 401


# --------------------------------------------------------------------------
# 4. Economy integrity
# --------------------------------------------------------------------------


async def test_replayed_activity_is_credited_once(client, auth_headers):
    payload = _activity_payload()

    first = await client.post("/api/v1/activities/sync", json=payload, headers=auth_headers)
    assert first.status_code == 200, first.text
    assert first.json()["duplicate"] is False
    earned = first.json()["stamina_earned"]
    assert earned > 0

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    balance_after_first = me.json()["stamina_balance"]

    for _ in range(5):
        again = await client.post(
            "/api/v1/activities/sync", json=payload, headers=auth_headers
        )
        assert again.status_code == 200
        assert again.json()["duplicate"] is True

    me2 = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me2.json()["stamina_balance"] == balance_after_first


async def test_overlapping_time_windows_are_rejected(client, auth_headers):
    base = _activity_payload()
    first = await client.post("/api/v1/activities/sync", json=base, headers=auth_headers)
    assert first.status_code == 200

    # Same window, different idempotency key - must still be refused.
    overlapping = _activity_payload(
        client_activity_uuid=str(uuid.uuid4()),
        start_time=base["start_time"],
        end_time=base["end_time"],
    )
    resp = await client.post(
        "/api/v1/activities/sync", json=overlapping, headers=auth_headers
    )
    assert resp.status_code == 409


async def test_streak_advances_once_per_day(client, auth_headers):
    now = datetime.now(timezone.utc)
    for i in range(3):
        payload = _activity_payload(
            client_activity_uuid=str(uuid.uuid4()),
            start_time=(now - timedelta(hours=(i + 1) * 3)).isoformat(),
            end_time=(now - timedelta(hours=(i + 1) * 3 - 1)).isoformat(),
            total_steps=3000,
        )
        resp = await client.post(
            "/api/v1/activities/sync", json=payload, headers=auth_headers
        )
        assert resp.status_code == 200, resp.text

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me.json()["streak_days"] == 1


async def test_daily_cap_limits_total_earnings(client, auth_headers):
    """Many large uploads in one day must saturate rather than accumulate."""
    now = datetime.now(timezone.utc)
    for i in range(12):
        payload = _activity_payload(
            client_activity_uuid=str(uuid.uuid4()),
            start_time=(now - timedelta(hours=(i + 1) * 1.5)).isoformat(),
            end_time=(now - timedelta(hours=(i + 1) * 1.5 - 1)).isoformat(),
            total_steps=40_000,
            elevation_gain_m=100.0,
        )
        await client.post("/api/v1/activities/sync", json=payload, headers=auth_headers)

    from app.core.config import settings

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    earned = me.json()["stamina_balance"] - 100  # starting balance
    assert earned <= settings.DAILY_STAMINA_CAP


async def test_future_dated_activity_is_rejected(client, auth_headers):
    now = datetime.now(timezone.utc)
    payload = _activity_payload(
        start_time=(now + timedelta(days=1)).isoformat(),
        end_time=(now + timedelta(days=1, hours=2)).isoformat(),
    )
    resp = await client.post("/api/v1/activities/sync", json=payload, headers=auth_headers)
    assert resp.status_code == 400


async def test_inverted_time_window_is_rejected(client, auth_headers):
    now = datetime.now(timezone.utc)
    payload = _activity_payload(
        start_time=now.isoformat(), end_time=(now - timedelta(hours=1)).isoformat()
    )
    resp = await client.post("/api/v1/activities/sync", json=payload, headers=auth_headers)
    assert resp.status_code == 422


async def test_cannot_mint_from_another_users_activity(client, auth_headers):
    """Ownership on /marketplace/mint must be enforced server-side."""
    mine = await client.post(
        "/api/v1/activities/sync", json=_activity_payload(), headers=auth_headers
    )
    activity_id = mine.json()["activity_id"]

    attacker = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "attacker",
            "email": "attacker@example.com",
            "password": "AttackerPassword1!",
        },
    )
    attacker_headers = {"Authorization": f"Bearer {attacker.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/marketplace/mint",
        headers=attacker_headers,
        json={
            "activity_id": activity_id,
            "title": "Stolen Summit",
            "original_photo_url": "https://example.com/p.jpg",
            "location_name": "Somewhere",
        },
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------
# 5. Configuration hardening
# --------------------------------------------------------------------------


async def test_cors_wildcard_is_refused_by_config():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="x" * 40,
            BACKEND_CORS_ORIGINS=["*"],  # type: ignore[arg-type]
        )


async def test_placeholder_secret_key_is_refused():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="gremlins-super-secret-production-key-change-in-prod-2026")


async def test_security_headers_present(client):
    resp = await client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
