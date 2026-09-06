from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.activity import ActivityRecord
    from app.models.gremlin import Gremlin
    from app.models.nft import NFTListing


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String)
    solana_wallet: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)

    # Reputation & Verification
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_device_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    reputation_score: Mapped[float] = mapped_column(Float, default=100.0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    streak_freeze_count: Mapped[int] = mapped_column(Integer, default=2)
    # Calendar day the streak last advanced, so it cannot be inflated by
    # repeatedly calling /activities/sync.
    last_streak_date: Mapped[Optional[date]] = mapped_column(Date)
    last_active_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Soft & Hard Balances
    stamina_balance: Mapped[int] = mapped_column(Integer, default=100)
    grln_token_balance: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    gremlins: Mapped[List["Gremlin"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    activities: Mapped[List["ActivityRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    nft_listings: Mapped[List["NFTListing"]] = relationship(
        back_populates="seller", foreign_keys="NFTListing.seller_id"
    )
