from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.nft import NFTMetadata
    from app.models.user import User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActivityRecord(Base):
    __tablename__ = "activity_records"
    __table_args__ = (
        # NULLs stay distinct in SQL, so clients that omit the key are simply
        # not deduplicated - they are not blocked.
        UniqueConstraint(
            "user_id", "client_activity_uuid", name="uq_activity_user_client_uuid"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Client-generated idempotency key. Unique per user, so replaying the same
    # upload cannot be credited twice.
    client_activity_uuid: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    # Activity Metrics
    activity_type: Mapped[str] = mapped_column(String, default="hiking")
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    calories_burned: Mapped[int] = mapped_column(Integer, default=0)

    # Wall-clock window the activity covers, used for overlap detection.
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    # Elevation & Biome
    start_elevation_m: Mapped[float] = mapped_column(Float, default=0.0)
    max_elevation_m: Mapped[float] = mapped_column(Float, default=0.0)
    elevation_gain_m: Mapped[float] = mapped_column(Float, default=0.0)
    detected_biome: Mapped[str] = mapped_column(String, default="common")
    weather_condition: Mapped[str] = mapped_column(String, default="clear")
    temperature_c: Mapped[float] = mapped_column(Float, default=20.0)

    # Anti-Cheat & Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100
    cadence_variance: Mapped[float] = mapped_column(Float, default=0.0)
    hardware_signature_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    ble_pack_count: Mapped[int] = mapped_column(Integer, default=0)
    flagged_reason: Mapped[Optional[str]] = mapped_column(String)

    # What was actually credited after daily caps were applied.
    steps_credited: Mapped[int] = mapped_column(Integer, default=0)
    stamina_credited: Mapped[int] = mapped_column(Integer, default=0)
    xp_credited: Mapped[int] = mapped_column(Integer, default=0)

    # Geo Data (Privacy Safe - home redacted)
    route_geojson: Mapped[Optional[Any]] = mapped_column(JSON)
    h3_hex_indexes: Mapped[List[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="activities")
    nft: Mapped[Optional["NFTMetadata"]] = relationship(
        back_populates="activity", uselist=False
    )
