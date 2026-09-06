import uuid
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.asyncio


async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["environment"] == "development"


async def test_user_registration_and_gremlin_creation(client):
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "hiker_pro",
            "email": "hiker@gremlins.health",
            "password": "StrongPassword2026!",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    token_data = reg_resp.json()
    assert "access_token" in token_data
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    # Gremlin auto-creation
    grem_resp = await client.get("/api/v1/gremlins/my", headers=headers)
    assert grem_resp.status_code == 200
    gremlin = grem_resp.json()
    assert gremlin["level"] == 1
    assert gremlin["hp"] == 100

    # Sync activity
    now = datetime.now(timezone.utc)
    sync_resp = await client.post(
        "/api/v1/activities/sync",
        headers=headers,
        json={
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
        },
    )
    assert sync_resp.status_code == 200, sync_resp.text
    activity_data = sync_resp.json()
    assert activity_data["is_verified"] is True
    assert activity_data["detected_biome"] == "mountain_frost"
    assert activity_data["gremlin_xp_gained"] > 0
    assert activity_data["duplicate"] is False


async def test_password_hash_roundtrip_and_upgrade():
    from app.core.security import get_password_hash, needs_rehash, verify_password

    hashed = get_password_hash("CorrectHorseBattery1!")
    assert verify_password("CorrectHorseBattery1!", hashed)
    assert not verify_password("wrong", hashed)
    assert not needs_rehash(hashed)

    # Legacy '<salt>$<hex>' rows must keep working and be flagged for upgrade.
    import hashlib

    salt = "a" * 32
    legacy_key = hashlib.pbkdf2_hmac("sha256", b"legacy-pass", salt.encode(), 100_000)
    legacy = f"{salt}${legacy_key.hex()}"
    assert verify_password("legacy-pass", legacy)
    assert needs_rehash(legacy)


async def test_feeding_costs_stamina(client, auth_headers):
    before = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
    resp = await client.post(
        "/api/v1/gremlins/feed", json={"food_type": "energy_berry"}, headers=auth_headers
    )
    assert resp.status_code == 200
    after = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
    assert after["stamina_balance"] == before["stamina_balance"] - 15


async def test_feeding_without_stamina_is_refused(client, auth_headers):
    # Starting balance is 100; six feeds cost 90, the seventh must fail.
    for _ in range(6):
        await client.post(
            "/api/v1/gremlins/feed",
            json={"food_type": "energy_berry"},
            headers=auth_headers,
        )
    resp = await client.post(
        "/api/v1/gremlins/feed", json={"food_type": "energy_berry"}, headers=auth_headers
    )
    assert resp.status_code == 400
