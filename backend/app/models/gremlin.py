from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiomeType(str, Enum):
    COMMON = "common"
    MOUNTAIN_FROST = "mountain_frost"
    FOREST_GUARDIAN = "forest_guardian"
    CYBER_SHADOW = "cyber_shadow"
    STORMBRINGER = "stormbringer"
    DESERT_SOLAR = "desert_solar"


class GremlinRarity(str, Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"


class Gremlin(Base):
    __tablename__ = "gremlins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, default="Gremly")

    # Tamagotchi & Evolution Stats
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    next_level_xp: Mapped[int] = mapped_column(Integer, default=1000)
    hp: Mapped[int] = mapped_column(Integer, default=100)
    max_hp: Mapped[int] = mapped_column(Integer, default=100)
    hunger: Mapped[int] = mapped_column(Integer, default=0)  # 0 (full) .. 100 (starving)
    mood: Mapped[int] = mapped_column(Integer, default=100)  # 100 (happy) .. 0 (depressed)
    is_sleeping: Mapped[bool] = mapped_column(Boolean, default=False)

    # Biome & Traits
    rarity: Mapped[str] = mapped_column(String, default=GremlinRarity.COMMON.value)
    biome_affinity: Mapped[str] = mapped_column(String, default=BiomeType.COMMON.value)
    biome_resonance_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Dynamic Visual Attributes
    avatar_image_url: Mapped[str] = mapped_column(
        String, default="/assets/gremlins/egg_base.webp"
    )
    equipped_gear: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=lambda: {"hat": None, "shoes": None, "amulet": None}
    )
    visual_traits: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {"horns": "none", "wings": "none", "aura": "none", "skin": "default"},
    )

    # On-chain linkage
    solana_cnft_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    tree_address: Mapped[Optional[str]] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_fed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_evolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="gremlins")
