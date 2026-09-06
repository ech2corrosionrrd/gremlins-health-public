"""
Tests for linking a Solana wallet.

solana_wallet is a UNIQUE column, and the first version of this endpoint
wrote to it with no validation and no conflict handling: a duplicate address
produced an unhandled IntegrityError (HTTP 500), and any 32-character string
was accepted as an address.
"""
import pytest

pytestmark = pytest.mark.asyncio

VALID = "7cVfgArCheMR6Cs4t6vz5rfnqd56vZq4ndaG9m5dXKUS"
VALID_OTHER = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"


async def _register(client, name):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": name,
            "email": f"{name}@example.com",
            "password": "StrongPassword2026!",
        },
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_valid_address_is_linked(client, auth_headers):
    resp = await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["solana_wallet"] == VALID


@pytest.mark.parametrize(
    "bad",
    [
        "!" * 40,               # not base58 at all
        "0OIl" + "1" * 36,      # the four characters base58 excludes
        "short",                # too short
        "1" * 60,               # too long for a 32-byte key
        "",                     # empty - what the disconnect button used to send
    ],
)
async def test_invalid_addresses_are_rejected(client, auth_headers, bad):
    resp = await client.post(
        "/api/v1/users/wallet", json={"wallet_address": bad}, headers=auth_headers
    )
    assert resp.status_code == 422, f"accepted {bad!r}"


async def test_duplicate_address_is_a_conflict_not_a_crash(client, auth_headers):
    first = await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=auth_headers
    )
    assert first.status_code == 200

    other = await _register(client, "second_hiker")
    resp = await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=other
    )
    assert resp.status_code == 409, resp.text


async def test_relinking_the_same_address_is_idempotent(client, auth_headers):
    for _ in range(3):
        resp = await client.post(
            "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["solana_wallet"] == VALID


async def test_user_can_switch_to_another_address(client, auth_headers):
    await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=auth_headers
    )
    resp = await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID_OTHER}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["solana_wallet"] == VALID_OTHER


async def test_unlink_frees_the_address_for_someone_else(client, auth_headers):
    await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=auth_headers
    )

    resp = await client.delete("/api/v1/users/wallet", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["solana_wallet"] is None

    other = await _register(client, "third_hiker")
    resp = await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}, headers=other
    )
    assert resp.status_code == 200


async def test_wallet_endpoints_require_authentication(client):
    assert (await client.post(
        "/api/v1/users/wallet", json={"wallet_address": VALID}
    )).status_code in (401, 403)
    assert (await client.delete("/api/v1/users/wallet")).status_code in (401, 403)
