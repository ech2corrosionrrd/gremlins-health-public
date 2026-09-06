"""
Контракт, на який тепер спирається UI.

До цього фронтенд мінтив локально: SecureCamera збирала NFT-обʼєкт у браузері,
Marketplace показував initialNFTs, а RaidBoss — initialQuests. Ендпоінти
існували, але їх ніхто не викликав, тож ці шляхи не були покриті.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.asyncio


async def _verified_activity(client, headers, steps=12500, gain=850.0):
    now = datetime.now(timezone.utc)
    resp = await client.post(
        "/api/v1/activities/sync",
        headers=headers,
        json={
            "client_activity_uuid": str(uuid.uuid4()),
            "start_time": (now - timedelta(hours=3)).isoformat(),
            "end_time": (now - timedelta(hours=1)).isoformat(),
            "total_steps": steps,
            "total_distance_km": 8.5,
            "elevation_gain_m": gain,
            "max_elevation_m": 1650.0,
            "weather_condition": "clear",
            "temperature_c": 14.0,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_verified"] is True
    return body["activity_id"]


async def _mint(client, headers, activity_id, title="Adventure #4242"):
    return await client.post(
        "/api/v1/marketplace/mint",
        headers=headers,
        json={
            "activity_id": activity_id,
            "title": title,
            "story_note": "Proof of Adventure.",
            "original_photo_url": "data:image/jpeg;base64,AAAA",
            "location_name": "Trail Waypoint (1650m)",
        },
    )


async def test_mint_returns_the_fields_the_ui_maps(client, auth_headers):
    activity_id = await _verified_activity(client, auth_headers)
    resp = await _mint(client, auth_headers, activity_id)
    assert resp.status_code == 201, resp.text
    nft = resp.json()

    # toNFTItem() у lib/api.ts читає саме ці поля.
    for field in (
        "id", "title", "location_name", "rarity",
        "original_photo_url", "rendered_art_url",
        "likes_count", "views_count", "is_onchain", "created_at", "attributes",
    ):
        assert field in nft, f"UI очікує поле {field}"

    # Мінт симульований, і відповідь мусить це визнавати.
    assert nft["is_onchain"] is False
    assert nft["solana_asset_id"].startswith("sim_")


async def test_rarity_is_decided_by_the_server_not_the_client(client, auth_headers):
    """Клієнт раніше сам собі писав rarity 'Epic'. Тепер вирішує бекенд."""
    small = await _verified_activity(client, auth_headers, steps=3000, gain=50.0)
    resp = await _mint(client, auth_headers, small, title="Short walk")
    assert resp.status_code == 201
    assert resp.json()["rarity"] == "Common"


async def test_one_nft_per_activity(client, auth_headers):
    activity_id = await _verified_activity(client, auth_headers)
    assert (await _mint(client, auth_headers, activity_id)).status_code == 201
    assert (await _mint(client, auth_headers, activity_id)).status_code == 409


async def test_explore_returns_listing_with_price_and_nested_nft(client, auth_headers):
    activity_id = await _verified_activity(client, auth_headers)
    nft = (await _mint(client, auth_headers, activity_id)).json()

    listed = await client.post(
        "/api/v1/marketplace/list",
        headers=auth_headers,
        json={"nft_id": nft["id"], "price_sol": 0.75},
    )
    assert listed.status_code == 201, listed.text

    explore = await client.get("/api/v1/marketplace/explore")
    assert explore.status_code == 200
    rows = explore.json()
    assert len(rows) == 1

    row = rows[0]
    # Ціна на лістингу, а не на NFT: Marketplace показує картку без цінника,
    # поки ассет не виставлений.
    assert row["price_sol"] == 0.75
    assert row["nft"]["id"] == nft["id"]
    assert row["nft"]["title"] == nft["title"]


async def test_explore_is_empty_until_something_is_listed(client, auth_headers):
    activity_id = await _verified_activity(client, auth_headers)
    await _mint(client, auth_headers, activity_id)

    explore = await client.get("/api/v1/marketplace/explore")
    assert explore.status_code == 200
    assert explore.json() == []


async def test_brand_quests_shape_matches_the_ui(client):
    from app.seed import seed

    await seed()
    resp = await client.get("/api/v1/quests/brand-bounties")
    assert resp.status_code == 200
    quests = resp.json()
    assert quests, "після сідингу має бути хоча б один квест"

    for field in (
        "id", "sponsor_brand", "brand_logo_url", "title", "description",
        "required_steps", "required_elevation_gain_m", "reward_pool_usdc",
        "reward_grln_tokens", "max_claimants", "current_claimants", "expires_at",
    ):
        assert field in quests[0], f"UI очікує поле {field}"


async def test_mint_requires_a_verified_activity(client, auth_headers):
    resp = await _mint(client, auth_headers, activity_id=99999)
    assert resp.status_code == 404
