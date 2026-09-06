use anchor_lang::prelude::*;

/// Program-wide configuration.
///
/// `oracle_authority` is the backend key that attests off-chain telemetry.
/// Progression instructions require its signature, because level, rarity and
/// step counts are all decided by the anti-cheat pipeline - not by the client.
#[account]
pub struct ProgramConfig {
    pub admin: Pubkey,
    pub oracle_authority: Pubkey,
    pub bump: u8,
}

impl ProgramConfig {
    pub const LEN: usize = 8 + 32 + 32 + 1;
    pub const SEED: &'static [u8] = b"program_config";
}

#[account]
pub struct UserProfile {
    pub authority: Pubkey,
    pub reputation_score: u16,
    pub total_steps: u64,
    pub total_elevation_m: u32,
    pub completed_trails_count: u32,
    pub streak_days: u16,
    /// Monotonic counter of accepted attestations. The oracle includes the
    /// expected value in each instruction, so a signed payload cannot be
    /// replayed to credit the same hike twice.
    pub attestation_nonce: u64,
    pub bump: u8,
}

impl UserProfile {
    pub const LEN: usize = 8 + 32 + 2 + 8 + 4 + 4 + 2 + 8 + 1;
    pub const SEED: &'static [u8] = b"user_profile";
}

#[account]
pub struct GremlinAccount {
    pub owner: Pubkey,
    pub level: u8,
    pub rarity: u8,         // 0: Common, 1: Uncommon, 2: Rare, 3: Epic, 4: Legendary
    pub biome_affinity: u8, // 0: Common, 1: MountainFrost, 2: Forest, 3: CyberShadow, 4: Storm
    pub total_xp: u64,
    pub last_evolved_ts: i64,
    pub bump: u8,
}

impl GremlinAccount {
    pub const LEN: usize = 8 + 32 + 1 + 1 + 1 + 8 + 8 + 1;
    pub const SEED: &'static [u8] = b"gremlin_companion";

    /// Highest level the program will accept. Bounds an oracle bug or a
    /// compromised key to something recoverable.
    pub const MAX_LEVEL: u8 = 100;
    /// Rarity is an enum discriminant, not free-form data.
    pub const MAX_RARITY: u8 = 4;
    pub const MAX_BIOME: u8 = 5;
}

#[account]
pub struct MarketplaceFeePool {
    pub authority: Pubkey,
    pub team_treasury: Pubkey,
    pub prize_pool_treasury: Pubkey,
    pub total_volume_sol: u64,
    pub total_tokens_burned: u64,
    pub bump: u8,
}

impl MarketplaceFeePool {
    pub const LEN: usize = 8 + 32 + 32 + 32 + 8 + 8 + 1;
}
