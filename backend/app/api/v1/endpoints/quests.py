from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.quest import BrandQuest, ClanRaidBoss
from app.schemas.quest import BrandQuestResponse, ClanRaidBossResponse

router = APIRouter()


@router.get("/brand-bounties", response_model=List[BrandQuestResponse])
async def get_brand_quests(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Active sponsored quests.

    Read-only: the previous version inserted demo rows when the table was
    empty, which let any anonymous GET write to the database. Seed data now
    comes from `python -m app.seed`.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    res = await db.execute(
        select(BrandQuest)
        .where(BrandQuest.expires_at > now)
        .order_by(BrandQuest.expires_at.asc())
        .limit(limit)
    )
    return [BrandQuestResponse.model_validate(q) for q in res.scalars().all()]


@router.get("/raid-boss", response_model=Optional[ClanRaidBossResponse])
async def get_current_raid_boss(db: AsyncSession = Depends(get_db)):
    """Returns the active raid boss, or null when no raid is running."""
    res = await db.execute(
        select(ClanRaidBoss)
        .where(ClanRaidBoss.is_defeated.is_(False))
        .order_by(ClanRaidBoss.starts_at.desc())
        .limit(1)
    )
    boss = res.scalar_one_or_none()
    return ClanRaidBossResponse.model_validate(boss) if boss else None
