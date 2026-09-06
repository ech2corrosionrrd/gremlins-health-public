from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.gremlin import Gremlin
from app.models.user import User
from app.schemas.gremlin import GremlinFeedRequest, GremlinResponse
from app.services.evolution_service import EvolutionService

router = APIRouter()

FEED_STAMINA_COST = 15


async def _get_owned_gremlin(db: AsyncSession, user: User) -> Gremlin:
    res = await db.execute(select(Gremlin).where(Gremlin.owner_id == user.id).limit(1))
    gremlin = res.scalar_one_or_none()
    if not gremlin:
        raise HTTPException(status_code=404, detail="Gremlin not found")
    return gremlin


@router.get("/my", response_model=GremlinResponse)
async def get_my_gremlin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Gremlin).where(Gremlin.owner_id == current_user.id).limit(1)
    )
    gremlin = res.scalar_one_or_none()
    if not gremlin:
        # Self-heal for accounts created before the starter Gremlin existed.
        gremlin = Gremlin(owner_id=current_user.id, name="Gremly")
        db.add(gremlin)
        await db.commit()
        await db.refresh(gremlin)
    return GremlinResponse.model_validate(gremlin)


@router.post("/feed", response_model=GremlinResponse)
async def feed_gremlin(
    feed_req: GremlinFeedRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gremlin = await _get_owned_gremlin(db, current_user)

    if current_user.stamina_balance < FEED_STAMINA_COST:
        raise HTTPException(
            status_code=400, detail="Not enough stamina balance. Go for a walk!"
        )

    current_user.stamina_balance -= FEED_STAMINA_COST
    gremlin.hunger = max(0, gremlin.hunger - 35)
    gremlin.mood = min(100, gremlin.mood + 20)
    gremlin.hp = min(gremlin.max_hp, gremlin.hp + 15)
    gremlin.last_fed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(gremlin)
    return GremlinResponse.model_validate(gremlin)


@router.post("/evolve", response_model=GremlinResponse)
async def evolve_gremlin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gremlin = await _get_owned_gremlin(db, current_user)

    # Guard before mutating. The previous version ran unconditionally and set
    # hp = max_hp at the end, so calling /evolve was a free full heal even
    # when no level-up was earned.
    if gremlin.xp < gremlin.next_level_xp:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Not enough XP to evolve "
                f"({gremlin.xp}/{gremlin.next_level_xp})"
            ),
        )

    new_level, rem_xp, next_xp, rarity, traits = EvolutionService.apply_evolution_check(
        gremlin.level, gremlin.xp, gremlin.next_level_xp, gremlin.biome_affinity
    )

    gremlin.level = new_level
    gremlin.xp = rem_xp
    gremlin.next_level_xp = next_xp
    gremlin.rarity = rarity
    gremlin.visual_traits = traits
    gremlin.max_hp = 100 + (new_level * 10)
    gremlin.hp = gremlin.max_hp  # a genuine level-up does restore health
    gremlin.last_evolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(gremlin)
    return GremlinResponse.model_validate(gremlin)
