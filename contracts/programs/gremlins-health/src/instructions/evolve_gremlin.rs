use anchor_lang::prelude::*;

use crate::errors::GremlinError;
use crate::state::{GremlinAccount, ProgramConfig, UserProfile};

/// Applies an evolution that the backend anti-cheat pipeline has already
/// verified.
///
/// The client cannot call this on its own: `oracle_authority` must sign, and
/// it must match the key stored in ProgramConfig. Previously every field was
/// taken straight from instruction data with only `new_level > level` as a
/// check, so any wallet could promote itself to a max-level Legendary.
#[derive(Accounts)]
pub struct EvolveGremlin<'info> {
    #[account(
        seeds = [ProgramConfig::SEED],
        bump = config.bump,
    )]
    pub config: Account<'info, ProgramConfig>,

    #[account(
        mut,
        seeds = [UserProfile::SEED, owner.key().as_ref()],
        bump = user_profile.bump,
        constraint = user_profile.authority == owner.key() @ GremlinError::UnauthorizedGremlinOwner,
    )]
    pub user_profile: Account<'info, UserProfile>,

    #[account(
        mut,
        seeds = [GremlinAccount::SEED, owner.key().as_ref()],
        bump = gremlin_account.bump,
        constraint = gremlin_account.owner == owner.key() @ GremlinError::UnauthorizedGremlinOwner,
    )]
    pub gremlin_account: Account<'info, GremlinAccount>,

    /// The player. Identifies whose Gremlin this is; does not need to sign,
    /// because the oracle's signature is what authorises the change.
    /// CHECK: only used as a PDA seed and compared against stored owners.
    pub owner: UncheckedAccount<'info>,

    #[account(
        constraint = oracle_authority.key() == config.oracle_authority
            @ GremlinError::InvalidTelemetryProof,
    )]
    pub oracle_authority: Signer<'info>,
}

pub fn handler(
    ctx: Context<EvolveGremlin>,
    expected_nonce: u64,
    new_level: u8,
    new_rarity: u8,
    new_biome_affinity: u8,
    gained_xp: u64,
) -> Result<()> {
    let profile = &mut ctx.accounts.user_profile;

    // Replay guard: a signed attestation is valid for exactly one nonce.
    require!(
        profile.attestation_nonce == expected_nonce,
        GremlinError::StaleAttestation
    );

    let gremlin = &mut ctx.accounts.gremlin_account;
    let previous_level = gremlin.level;

    require!(new_level > previous_level, GremlinError::InsufficientXpForEvolution);
    require!(
        new_level <= GremlinAccount::MAX_LEVEL,
        GremlinError::MaxLevelReached
    );
    require!(
        new_rarity <= GremlinAccount::MAX_RARITY,
        GremlinError::InvalidTraitValue
    );
    require!(
        new_biome_affinity <= GremlinAccount::MAX_BIOME,
        GremlinError::InvalidTraitValue
    );
    // Rarity is derived from level, so it may rise but never fall.
    require!(new_rarity >= gremlin.rarity, GremlinError::InvalidTraitValue);

    gremlin.level = new_level;
    gremlin.rarity = new_rarity;
    gremlin.biome_affinity = new_biome_affinity;
    gremlin.total_xp = gremlin
        .total_xp
        .checked_add(gained_xp)
        .ok_or(GremlinError::MathOverflow)?;
    gremlin.last_evolved_ts = Clock::get()?.unix_timestamp;

    profile.attestation_nonce = profile
        .attestation_nonce
        .checked_add(1)
        .ok_or(GremlinError::MathOverflow)?;

    msg!(
        "Gremlin evolved: level {} -> {}, rarity {}",
        previous_level,
        new_level,
        new_rarity
    );
    Ok(())
}
