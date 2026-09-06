export type BiomeType = 'common' | 'mountain_frost' | 'forest_guardian' | 'cyber_shadow' | 'stormbringer' | 'desert_solar';
export type GremlinRarity = 'Common' | 'Uncommon' | 'Rare' | 'Epic' | 'Legendary';

export interface UserProfile {
  id: number;
  username: string;
  telegram_id?: string;
  solana_wallet?: string;
  is_device_verified: boolean;
  reputation_score: number;
  streak_days: number;
  streak_freeze_count: number;
  stamina_balance: number;
  grln_token_balance: number;
}

export interface Gremlin {
  id: number;
  owner_id: number;
  name: string;
  level: number;
  xp: number;
  next_level_xp: number;
  hp: number;
  max_hp: number;
  hunger: number;
  mood: number;
  is_sleeping: boolean;
  rarity: GremlinRarity;
  biome_affinity: BiomeType;
  biome_resonance_score: number;
  avatar_image_url: string;
  visual_traits: {
    horns: string;
    wings: string;
    aura: string;
    skin: string;
  };
}

export interface ActivitySyncResult {
  activity_id: number;
  is_verified: boolean;
  verification_score: number;
  steps_credited: number;
  stamina_earned: number;
  gremlin_xp_gained: number;
  detected_biome: BiomeType;
  biome_resonance_bonus: number;
  unlocked_h3_tiles_count: number;
  flagged_reason?: string;
}

export interface NFTItem {
  id: number;
  title: string;
  story_note?: string;
  location_name: string;
  rarity: GremlinRarity;
  original_photo_url: string;
  rendered_art_url: string;
  solana_asset_id?: string;
  likes_count: number;
  views_count: number;
  price_sol?: number;
  price_usd_approx?: number;
  is_verified: boolean;
  /**
   * Чи існує ассет у мережі. Бекенд поки що мінтить симульовано й повертає
   * false — UI мусить це показувати, а не видавати за справжній мінт.
   */
  is_onchain?: boolean;
  created_at: string;
  attributes: {
    Location: string;
    Biome: string;
    Rarity: string;
    Elevation_m: number;
    Weather: string;
  };
}

export interface BrandQuest {
  id: number;
  sponsor_brand: string;
  brand_logo_url: string;
  title: string;
  description: string;
  required_biome?: string;
  required_steps: number;
  required_elevation_gain_m: number;
  reward_pool_usdc: number;
  reward_grln_tokens: number;
  reward_gear_skin_id?: string;
  max_claimants: number;
  current_claimants: number;
  expires_at: string;
}

export interface ClanRaidBoss {
  id: number;
  boss_name: string;
  total_health_steps: number;
  current_health_steps: number;
  is_defeated: boolean;
  reward_grln_pool: number;
  ends_at: string;
}
