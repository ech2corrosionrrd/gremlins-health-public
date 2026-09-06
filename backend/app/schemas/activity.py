from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

# A single upload is capped well above any real hike but far below the point
# where telemetry parsing becomes a memory concern.
MAX_TELEMETRY_SAMPLES = 20_000


class TelemetryDataPoint(BaseModel):
    timestamp_ms: int = Field(..., ge=0)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    altitude_m: float = Field(..., ge=-500.0, le=9000.0)
    speed_kmh: float = Field(..., ge=0.0, le=2000.0)
    cadence_spm: int = Field(..., ge=0, le=1000)
    heart_rate_bpm: Optional[int] = Field(None, ge=0, le=300)


class ActivitySyncRequest(BaseModel):
    # Idempotency key. Send a stable per-activity UUID so a retried upload is
    # recognised instead of credited twice.
    client_activity_uuid: Optional[str] = Field(None, min_length=8, max_length=64)

    activity_type: str = Field("hiking", max_length=32)
    start_time: datetime
    end_time: datetime
    total_steps: int = Field(..., ge=0, le=500_000)
    total_distance_km: float = Field(..., ge=0.0, le=1000.0)
    elevation_gain_m: float = Field(0.0, ge=0.0, le=20_000.0)
    start_elevation_m: float = Field(0.0, ge=-500.0, le=9000.0)
    max_elevation_m: float = Field(0.0, ge=-500.0, le=9000.0)
    weather_condition: str = Field("clear", max_length=32)
    temperature_c: float = Field(18.0, ge=-90.0, le=60.0)

    # Telemetry for Anti-Cheat
    telemetry_samples: List[TelemetryDataPoint] = Field(
        default_factory=list, max_length=MAX_TELEMETRY_SAMPLES
    )
    device_integrity_token: Optional[str] = Field(None, max_length=4096)
    ble_nearby_devices_count: int = Field(0, ge=0, le=500)

    @model_validator(mode="after")
    def _check_window(self) -> "ActivitySyncRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ActivitySyncResponse(BaseModel):
    activity_id: int
    is_verified: bool
    verification_score: float
    steps_credited: int
    stamina_earned: int
    gremlin_xp_gained: int
    detected_biome: str
    biome_resonance_bonus: float
    unlocked_h3_tiles_count: int
    flagged_reason: Optional[str] = None
    # True when this upload matched an existing record and nothing was
    # credited again.
    duplicate: bool = False
    # Set when a daily cap trimmed the reward.
    capped_reason: Optional[str] = None
