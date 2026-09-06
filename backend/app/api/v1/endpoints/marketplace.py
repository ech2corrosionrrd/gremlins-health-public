from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import ActivityRecord
from app.models.nft import NFTListing, NFTMetadata
from app.models.user import User
from app.schemas.nft import (
    NFTListingCreate,
    NFTListingResponse,
    NFTMintRequest,
    NFTResponse,
)
from app.services.mock_ai_render_service import MockAIRenderService
from app.services.mock_solana_service import MockSolanaService

router = APIRouter()

# Approximate SOL price used for display only. A real listing must price
# against an oracle (e.g. Pyth) rather than a constant baked into the code.
SOL_USD_DISPLAY_RATE = 150.0


def _rarity_for(activity: ActivityRecord) -> str:
    if activity.total_steps >= 50_000 or activity.elevation_gain_m >= 1500:
        return "Legendary"
    if activity.total_steps >= 25_000 or activity.elevation_gain_m >= 800:
        return "Epic"
    if activity.total_steps >= 10_000:
        return "Rare"
    return "Common"


@router.post("/mint", response_model=NFTResponse, status_code=status.HTTP_201_CREATED)
async def mint_adventure_nft(
    mint_req: NFTMintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mints an adventure NFT from a verified activity.

    NOTE: minting is currently SIMULATED - see MockSolanaService. The stored
    row is flagged is_onchain=False and the identifiers are not resolvable.
    """
    res = await db.execute(
        select(ActivityRecord).where(
            ActivityRecord.id == mint_req.activity_id,
            ActivityRecord.user_id == current_user.id,
        )
    )
    activity = res.scalar_one_or_none()
    # 404 rather than 403 for someone else's activity: do not confirm it exists.
    if not activity:
        raise HTTPException(status_code=404, detail="Activity record not found")

    if not activity.is_verified:
        raise HTTPException(
            status_code=400, detail="Cannot mint NFT from unverified activity"
        )

    # One NFT per activity - enforced by a unique column, checked here for a
    # clean error message.
    existing = await db.execute(
        select(NFTMetadata.id).where(NFTMetadata.activity_id == activity.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This activity has already been minted",
        )

    rarity = _rarity_for(activity)

    ai_result = MockAIRenderService.generate_artwork(
        original_photo_url=mint_req.original_photo_url,
        location_name=mint_req.location_name,
        biome_type=activity.detected_biome,
        rarity=rarity,
        elevation_m=activity.max_elevation_m,
        weather=activity.weather_condition,
    )

    solana_meta = MockSolanaService.simulate_mint_compressed_nft(
        creator_wallet=current_user.solana_wallet or "SimulatedWallet",
        title=mint_req.title,
        rendered_art_url=ai_result["rendered_art_url"],
        attributes=ai_result["attributes"],
    )

    nft = NFTMetadata(
        activity_id=activity.id,
        creator_id=current_user.id,
        title=mint_req.title,
        story_note=mint_req.story_note,
        location_name=mint_req.location_name,
        rarity=rarity,
        original_photo_url=mint_req.original_photo_url,
        rendered_art_url=ai_result["rendered_art_url"],
        arweave_metadata_uri=solana_meta["arweave_metadata_uri"],
        solana_asset_id=solana_meta["solana_asset_id"],
        mint_tx_hash=solana_meta["mint_tx_hash"],
        # Nothing was broadcast, so this must not claim otherwise.
        is_onchain=False,
        attributes=ai_result["attributes"],
    )
    db.add(nft)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This activity has already been minted",
        )
    await db.refresh(nft)

    return NFTResponse.model_validate(nft)


@router.get("/explore", response_model=List[NFTListingResponse])
async def get_marketplace_listings(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    res = await db.execute(
        select(NFTListing)
        .options(selectinload(NFTListing.nft))
        .where(NFTListing.is_sold.is_(False))
        .order_by(NFTListing.listed_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [NFTListingResponse.model_validate(listing) for listing in res.scalars().all()]


@router.post("/list", response_model=NFTListingResponse, status_code=status.HTTP_201_CREATED)
async def list_nft_for_sale(
    list_in: NFTListingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(NFTMetadata).where(
            NFTMetadata.id == list_in.nft_id,
            NFTMetadata.creator_id == current_user.id,
        )
    )
    nft = res.scalar_one_or_none()
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found or not owned")

    already = await db.execute(
        select(NFTListing).where(
            NFTListing.nft_id == nft.id, NFTListing.is_sold.is_(False)
        )
    )
    if already.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="NFT is already listed"
        )

    listing = NFTListing(
        nft_id=nft.id,
        seller_id=current_user.id,
        price_sol=list_in.price_sol,
        price_usd_approx=list_in.price_sol * SOL_USD_DISPLAY_RATE,
        is_sold=False,
    )
    db.add(listing)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="NFT is already listed"
        )

    res_full = await db.execute(
        select(NFTListing)
        .options(selectinload(NFTListing.nft))
        .where(NFTListing.id == listing.id)
    )
    return NFTListingResponse.model_validate(res_full.scalar_one())
