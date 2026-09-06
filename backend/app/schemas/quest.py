from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class BrandQuestResponse(BaseModel):
    id: int
    sponsor_brand: str
    brand_logo_url: str
    title: str
    description: str
    required_biome: Optional[str]
    required_steps: int
    required_elevation_gain_m: float
    reward_pool_usdc: float
    reward_grln_tokens: int
    reward_gear_skin_id: Optional[str]
    max_claimants: int
    current_claimants: int
    expires_at: datetime

    class Config:
        from_attributes = True


class ClanRaidBossResponse(BaseModel):
    id: int
    boss_name: str
    total_health_steps: int
    current_health_steps: int
    is_defeated: bool
    reward_grln_pool: int
    starts_at: datetime
    ends_at: datetime

    class Config:
        from_attributes = True
