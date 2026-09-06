from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class GremlinBase(BaseModel):
    name: str = "Gremly"


class GremlinCreate(GremlinBase):
    pass


class GremlinFeedRequest(BaseModel):
    food_type: str = "energy_berry" # energy_berry, mountain_herb, protein_snack


class GremlinResponse(GremlinBase):
    id: int
    owner_id: int
    level: int
    xp: int
    next_level_xp: int
    hp: int
    max_hp: int
    hunger: int
    mood: int
    is_sleeping: bool
    rarity: str
    biome_affinity: str
    biome_resonance_score: float
    avatar_image_url: str
    equipped_gear: Dict[str, Any]
    visual_traits: Dict[str, Any]
    solana_cnft_id: Optional[str] = None
    created_at: datetime
    last_fed_at: datetime

    class Config:
        from_attributes = True
