from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class NFTMintRequest(BaseModel):
    activity_id: int
    title: str = Field(..., max_length=100)
    story_note: Optional[str] = Field(None, max_length=280)
    original_photo_url: str
    location_name: str
    camera_hardware_signature: Optional[str] = None


class NFTResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: int
    creator_id: int
    title: str
    story_note: Optional[str]
    location_name: str
    rarity: str
    original_photo_url: str
    rendered_art_url: str
    solana_asset_id: Optional[str]
    arweave_metadata_uri: Optional[str]
    likes_count: int
    views_count: int
    # False while the asset only exists in the local simulation.
    is_onchain: bool
    created_at: datetime
    attributes: Dict[str, Any]


class NFTListingCreate(BaseModel):
    nft_id: int
    price_sol: float = Field(..., gt=0.0)


class NFTListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nft_id: int
    seller_id: int
    price_sol: float
    price_usd_approx: float
    is_sold: bool
    listed_at: datetime
    nft: NFTResponse
