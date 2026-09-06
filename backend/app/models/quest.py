from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BrandQuest(Base):
    __tablename__ = "brand_quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sponsor_brand: Mapped[str] = mapped_column(String, nullable=False)
    brand_logo_url: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Quest Requirements
    required_biome: Mapped[Optional[str]] = mapped_column(String)
    required_steps: Mapped[int] = mapped_column(Integer, default=25000)
    required_elevation_gain_m: Mapped[float] = mapped_column(Float, default=500.0)
    # {"lat": 48.16, "lng": 24.50, "radius_km": 15}
    target_geofence_center: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Rewards Pool
    reward_pool_usdc: Mapped[float] = mapped_column(Float, default=1000.0)
    reward_grln_tokens: Mapped[int] = mapped_column(Integer, default=50)
    reward_gear_skin_id: Mapped[Optional[str]] = mapped_column(String)
    max_claimants: Mapped[int] = mapped_column(Integer, default=100)
    current_claimants: Mapped[int] = mapped_column(Integer, default=0)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ClanRaidBoss(Base):
    __tablename__ = "clan_raid_bosses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    boss_name: Mapped[str] = mapped_column(String, default="Gorgoroth Trail Titan")
    total_health_steps: Mapped[int] = mapped_column(Integer, default=10_000_000)
    current_health_steps: Mapped[int] = mapped_column(Integer, default=10_000_000)
    is_defeated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    reward_grln_pool: Mapped[int] = mapped_column(Integer, default=25000)
    starts_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
