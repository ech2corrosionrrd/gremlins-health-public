"""
Seeds demo content (brand quests, an active raid boss).

Run explicitly:  python -m app.seed

This used to happen implicitly inside GET handlers, which meant an
unauthenticated read could write rows. Seeding is now a deliberate operation.
Idempotent: existing rows are left alone.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine
from app.models.quest import BrandQuest, ClanRaidBoss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(BrandQuest).where(BrandQuest.expires_at > now).limit(1)
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                BrandQuest(
                    sponsor_brand="Salomon Outdoor",
                    brand_logo_url="https://example.invalid/brands/salomon.png",
                    title="Chornohora Ridge Expedition (25km)",
                    description=(
                        "Summit Hoverla and reach Nesamovyte Lake. Unlock the "
                        "Mountain Frost Gremlin skin and a sponsor reward."
                    ),
                    required_biome="mountain_frost",
                    required_steps=28000,
                    required_elevation_gain_m=850.0,
                    reward_pool_usdc=2500.0,
                    reward_grln_tokens=100,
                    reward_gear_skin_id="salomon_trail_wings",
                    max_claimants=100,
                    current_claimants=0,
                    expires_at=now + timedelta(days=30),
                )
            )
            logger.info("Seeded demo brand quest.")
        else:
            logger.info("Brand quests already present; skipping.")

        boss_exists = await db.execute(
            select(ClanRaidBoss).where(ClanRaidBoss.is_defeated.is_(False)).limit(1)
        )
        if boss_exists.scalar_one_or_none() is None:
            db.add(
                ClanRaidBoss(
                    boss_name="Gorgoroth the Trail Titan",
                    total_health_steps=10_000_000,
                    current_health_steps=10_000_000,
                    is_defeated=False,
                    reward_grln_pool=50_000,
                    starts_at=now,
                    ends_at=now + timedelta(days=7),
                )
            )
            logger.info("Seeded demo raid boss.")
        else:
            logger.info("Active raid boss already present; skipping.")

        await db.commit()

    await engine.dispose()
    logger.info("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
