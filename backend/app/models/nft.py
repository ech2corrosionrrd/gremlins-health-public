from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.activity import ActivityRecord
    from app.models.user import User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NFTMetadata(Base):
    __tablename__ = "nft_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activity_records.id"), nullable=False, unique=True
    )
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    story_note: Mapped[Optional[str]] = mapped_column(String)
    location_name: Mapped[str] = mapped_column(String, nullable=False)
    rarity: Mapped[str] = mapped_column(String, default="Rare")

    # Visual & On-chain assets
    original_photo_url: Mapped[str] = mapped_column(String, nullable=False)
    rendered_art_url: Mapped[str] = mapped_column(String, nullable=False)
    arweave_metadata_uri: Mapped[Optional[str]] = mapped_column(String)
    solana_asset_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    mint_tx_hash: Mapped[Optional[str]] = mapped_column(String)
    # False while the asset only exists in the local simulation.
    is_onchain: Mapped[bool] = mapped_column(Boolean, default=False)

    # Attributes for Metaplex standard
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Likes & Social
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    views_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Relationships
    activity: Mapped["ActivityRecord"] = relationship(back_populates="nft")
    listing: Mapped[Optional["NFTListing"]] = relationship(
        back_populates="nft", uselist=False
    )


class NFTListing(Base):
    __tablename__ = "nft_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nft_id: Mapped[int] = mapped_column(
        ForeignKey("nft_metadata.id"), nullable=False, unique=True
    )
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    price_sol: Mapped[float] = mapped_column(Float, nullable=False)
    price_usd_approx: Mapped[float] = mapped_column(Float, nullable=False)
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    buyer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    listed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    nft: Mapped["NFTMetadata"] = relationship(back_populates="listing")
    seller: Mapped["User"] = relationship(
        foreign_keys=[seller_id], back_populates="nft_listings"
    )
