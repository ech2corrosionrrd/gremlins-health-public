import { UserProfile, Gremlin, NFTItem, BrandQuest, ClanRaidBoss } from '../types';

export const initialUser: UserProfile = {
  id: 1,
  username: "Global_Explorer",
  telegram_id: "77741289",
  solana_wallet: "8vHq...4w7Z",
  is_device_verified: true,
  reputation_score: 98.5,
  streak_days: 14,
  streak_freeze_count: 2,
  stamina_balance: 340,
  grln_token_balance: 145.5,
};

export const initialGremlin: Gremlin = {
  id: 1,
  owner_id: 1,
  name: "AeroGremlin",
  level: 4,
  xp: 1450,
  next_level_xp: 3375,
  hp: 130,
  max_hp: 140,
  hunger: 15,
  mood: 92,
  is_sleeping: false,
  rarity: "Rare",
  biome_affinity: "mountain_frost",
  biome_resonance_score: 84.0,
  avatar_image_url: "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=600&auto=format&fit=crop&q=80",
  visual_traits: {
    horns: "ice_crystals",
    wings: "storm_sparks",
    aura: "cosmic_mist",
    skin: "mountain_frost"
  }
};

export const initialNFTs: NFTItem[] = [
  {
    id: 101,
    title: "Alpine Ridge Dawn Peak",
    story_note: "Dawn summit at -2°C. 28k steps across the mountain ridge. Frost Gremlin awakened!",
    location_name: "Alpine Summit Vista",
    rarity: "Epic",
    original_photo_url: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
    rendered_art_url: "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800&auto=format&fit=crop&q=80",
    solana_asset_id: "cNFT_984f...a891",
    likes_count: 412,
    views_count: 3200,
    price_sol: 0.85,
    price_usd_approx: 127.5,
    is_verified: true,
    created_at: "2026-09-05",
    attributes: {
      Location: "Alpine Ridge",
      Biome: "mountain_frost",
      Rarity: "Epic",
      Elevation_m: 2150,
      Weather: "freezing_dawn"
    }
  },
  {
    id: 102,
    title: "Misty Lake Haven Trail",
    story_note: "Cloud shroud near the glacial lake. Pitch dark water with mystical atmosphere.",
    location_name: "Glacial Mountain Lake",
    rarity: "Rare",
    original_photo_url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
    rendered_art_url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop&q=80",
    solana_asset_id: "cNFT_312c...771e",
    likes_count: 188,
    views_count: 1420,
    price_sol: 0.35,
    price_usd_approx: 52.5,
    is_verified: true,
    created_at: "2026-09-03",
    attributes: {
      Location: "Glacial Lake",
      Biome: "stormbringer",
      Rarity: "Rare",
      Elevation_m: 1450,
      Weather: "thunderstorm"
    }
  },
  {
    id: 103,
    title: "Urban Skyline Night Run",
    story_note: "15km night sprint across the city hills under twilight fog.",
    location_name: "Panoramic City Overlook",
    rarity: "Uncommon",
    original_photo_url: "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=800&auto=format&fit=crop&q=80",
    rendered_art_url: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80",
    solana_asset_id: "cNFT_551a...998b",
    likes_count: 94,
    views_count: 850,
    price_sol: 0.15,
    price_usd_approx: 22.5,
    is_verified: true,
    created_at: "2026-09-01",
    attributes: {
      Location: "City Overlook",
      Biome: "cyber_shadow",
      Rarity: "Uncommon",
      Elevation_m: 240,
      Weather: "night_fog"
    }
  }
];

export const initialQuests: BrandQuest[] = [
  {
    id: 1,
    sponsor_brand: "Salomon Outdoor",
    brand_logo_url: "https://assets.gremlins.health/brands/salomon.png",
    title: "Global Trail Summit Expedition",
    description: "Climb any mountain trail (20,000+ steps, >800m ascent). Unlock Salomon Frost Wings + $25 USDC.",
    required_biome: "mountain_frost",
    required_steps: 20000,
    required_elevation_gain_m: 800,
    reward_pool_usdc: 2500,
    reward_grln_tokens: 150,
    reward_gear_skin_id: "salomon_frost_wings",
    max_claimants: 100,
    current_claimants: 24,
    expires_at: "2026-09-30"
  },
  {
    id: 2,
    sponsor_brand: "Garmin Endurance",
    brand_logo_url: "https://assets.gremlins.health/brands/garmin.png",
    title: "Heart-Rate Zone 4 Forest Sprint",
    description: "Complete 10km in outdoor terrain with verified micro-cadence variance. Earn Garmin Tech Visor.",
    required_biome: "forest_guardian",
    required_steps: 14000,
    required_elevation_gain_m: 350,
    reward_pool_usdc: 1500,
    reward_grln_tokens: 80,
    reward_gear_skin_id: "garmin_fēnix_amulet",
    max_claimants: 200,
    current_claimants: 78,
    expires_at: "2026-09-25"
  }
];

export const initialBoss: ClanRaidBoss = {
  id: 1,
  boss_name: "Gorgoroth the Global Titan",
  total_health_steps: 10000000,
  current_health_steps: 6840200,
  is_defeated: false,
  reward_grln_pool: 50000,
  ends_at: "2026-09-12"
};
