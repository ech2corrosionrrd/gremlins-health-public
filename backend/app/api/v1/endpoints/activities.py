import logging
from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.activity import ActivityRecord
from app.models.gremlin import Gremlin
from app.models.user import User
from app.schemas.activity import ActivitySyncRequest, ActivitySyncResponse
from app.services.anticheat_service import AntiCheatService
from app.services.evolution_service import EvolutionService

logger = logging.getLogger(__name__)
router = APIRouter()


def _as_naive_utc(dt: datetime) -> datetime:
    """Normalise to naive UTC so comparisons against stored values line up."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _to_response(activity: ActivityRecord, duplicate: bool = False) -> ActivitySyncResponse:
    return ActivitySyncResponse(
        activity_id=activity.id,
        is_verified=activity.is_verified,
        verification_score=activity.verification_score,
        steps_credited=activity.steps_credited,
        stamina_earned=activity.stamina_credited,
        gremlin_xp_gained=activity.xp_credited,
        detected_biome=activity.detected_biome,
        biome_resonance_bonus=1.25 if activity.detected_biome != "common" else 1.0,
        unlocked_h3_tiles_count=len(activity.h3_hex_indexes or []),
        flagged_reason=activity.flagged_reason,
        duplicate=duplicate,
    )


@router.post("/sync", response_model=ActivitySyncResponse)
async def sync_activity(
    activity_in: ActivitySyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    start = _as_naive_utc(activity_in.start_time)
    end = _as_naive_utc(activity_in.end_time)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # 0a. Idempotency - a replayed upload returns the original result.
    if activity_in.client_activity_uuid:
        existing = await db.execute(
            select(ActivityRecord).where(
                ActivityRecord.user_id == current_user.id,
                ActivityRecord.client_activity_uuid == activity_in.client_activity_uuid,
            )
        )
        prior = existing.scalar_one_or_none()
        if prior is not None:
            return _to_response(prior, duplicate=True)

    # 0b. Sanity-check the window itself.
    duration = int((end - start).total_seconds())
    if duration <= 0:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    if duration > settings.MAX_ACTIVITY_DURATION_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Activity longer than {settings.MAX_ACTIVITY_DURATION_SECONDS}s",
        )
    # Small tolerance for client clock skew; anything further ahead is forged.
    if start > now + timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Activity starts in the future")

    # 0c. Overlap - the same wall-clock time cannot be sold twice.
    overlap = await db.execute(
        select(ActivityRecord.id).where(
            ActivityRecord.user_id == current_user.id,
            ActivityRecord.started_at.is_not(None),
            ActivityRecord.ended_at.is_not(None),
            ActivityRecord.started_at < end,
            ActivityRecord.ended_at > start,
        ).limit(1)
    )
    if overlap.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time window overlaps an already recorded activity",
        )

    # 1. Anti-Cheat Evaluation
    is_valid, score, variance, err_reason = AntiCheatService.evaluate_activity(
        total_steps=activity_in.total_steps,
        duration_seconds=duration,
        elevation_gain_m=activity_in.elevation_gain_m,
        telemetry_samples=activity_in.telemetry_samples,
        device_integrity_token=activity_in.device_integrity_token,
        ble_pack_count=activity_in.ble_nearby_devices_count,
    )

    # 2. Biome Detection
    detected_biome = EvolutionService.detect_biome(
        max_elevation_m=activity_in.max_elevation_m,
        temperature_c=activity_in.temperature_c,
        weather_condition=activity_in.weather_condition,
        time_hour=start.hour,
    )

    # 3. Provisional rewards
    stamina, xp, biome_bonus = EvolutionService.calculate_rewards(
        total_steps=activity_in.total_steps,
        elevation_gain_m=activity_in.elevation_gain_m,
        detected_biome=detected_biome,
        verification_score=score,
    )

    steps_credited = activity_in.total_steps if is_valid else 0
    capped_reason: str | None = None

    # 4. Daily caps, evaluated against what was already credited today.
    if is_valid:
        day_start = datetime.combine(now.date(), time.min)
        totals = await db.execute(
            select(
                func.coalesce(func.sum(ActivityRecord.steps_credited), 0),
                func.coalesce(func.sum(ActivityRecord.stamina_credited), 0),
                func.coalesce(func.sum(ActivityRecord.xp_credited), 0),
            ).where(
                ActivityRecord.user_id == current_user.id,
                ActivityRecord.created_at >= day_start,
            )
        )
        steps_today, stamina_today, xp_today = totals.one()

        steps_room = max(0, settings.DAILY_STEP_CAP - int(steps_today))
        stamina_room = max(0, settings.DAILY_STAMINA_CAP - int(stamina_today))
        xp_room = max(0, settings.DAILY_XP_CAP - int(xp_today))

        if steps_credited > steps_room or stamina > stamina_room or xp > xp_room:
            capped_reason = "Daily earning cap reached"
            steps_credited = min(steps_credited, steps_room)
            stamina = min(stamina, stamina_room)
            xp = min(xp, xp_room)
    else:
        stamina, xp = 0, 0

    # 5. Persist
    activity = ActivityRecord(
        user_id=current_user.id,
        client_activity_uuid=activity_in.client_activity_uuid,
        activity_type=activity_in.activity_type,
        total_steps=activity_in.total_steps,
        total_distance_km=activity_in.total_distance_km,
        duration_seconds=duration,
        started_at=start,
        ended_at=end,
        start_elevation_m=activity_in.start_elevation_m,
        max_elevation_m=activity_in.max_elevation_m,
        elevation_gain_m=activity_in.elevation_gain_m,
        detected_biome=detected_biome,
        weather_condition=activity_in.weather_condition,
        temperature_c=activity_in.temperature_c,
        is_verified=is_valid,
        verification_score=score,
        cadence_variance=variance,
        hardware_signature_valid=bool(activity_in.device_integrity_token),
        ble_pack_count=activity_in.ble_nearby_devices_count,
        flagged_reason=err_reason,
        steps_credited=steps_credited,
        stamina_credited=stamina,
        xp_credited=xp,
        # TODO(h3): derive real tiles from telemetry_samples via the H3 index.
        # Left empty rather than returning fabricated hexes.
        h3_hex_indexes=[],
    )
    db.add(activity)

    if is_valid:
        current_user.stamina_balance += stamina

        # Streak advances once per calendar day, regardless of upload count.
        today = now.date()
        if current_user.last_streak_date != today:
            yesterday = today - timedelta(days=1)
            current_user.streak_days = (
                current_user.streak_days + 1
                if current_user.last_streak_date == yesterday
                else 1
            )
            current_user.last_streak_date = today

        res = await db.execute(
            select(Gremlin).where(Gremlin.owner_id == current_user.id).limit(1)
        )
        gremlin = res.scalar_one_or_none()
        if gremlin:
            gremlin.xp += xp
            gremlin.biome_affinity = detected_biome
            gremlin.biome_resonance_score += steps_credited / 1000

    await db.commit()
    await db.refresh(activity)

    response = _to_response(activity)
    response.biome_resonance_bonus = biome_bonus
    response.capped_reason = capped_reason
    return response
