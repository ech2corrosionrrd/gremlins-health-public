use anchor_lang::prelude::*;

use crate::errors::GremlinError;
use crate::state::{ProgramConfig, UserProfile};

/// Records a completed adventure against the user's on-chain profile.
///
/// IMPORTANT - this instruction does NOT mint a compressed NFT yet.
///
/// The original version was named as though it did, listed mpl-bubblegum and
/// spl-account-compression as dependencies, and then never imported either:
/// it only incremented counters, and any wallet could call it in a loop to
/// inflate its own step total. Both problems are fixed here (oracle signature
/// plus a nonce), and the misleading part is stated plainly rather than
/// implied away.
///
/// Issuing the actual cNFT requires a CPI into Metaplex Bubblegum with a
/// Merkle tree, a tree authority PDA, the log wrapper and the compression
/// program. That work is tracked separately; until it lands, minting happens
/// off-chain in the backend and is flagged as simulated.
#[derive(Accounts)]
pub struct RecordAdventure<'info> {
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

    /// CHECK: only used as a PDA seed and compared against user_profile.authority.
    pub owner: UncheckedAccount<'info>,

    /// Only the backend oracle may credit steps - they come from verified
    /// telemetry, never from the client.
    #[account(
        constraint = oracle_authority.key() == config.oracle_authority
            @ GremlinError::InvalidTelemetryProof,
    )]
    pub oracle_authority: Signer<'info>,
}

pub fn handler(
    ctx: Context<RecordAdventure>,
    expected_nonce: u64,
    steps_walked: u64,
    elevation_gain_m: u32,
    _metadata_uri: String,
) -> Result<()> {
    let profile = &mut ctx.accounts.user_profile;

    require!(
        profile.attestation_nonce == expected_nonce,
        GremlinError::StaleAttestation
    );

    // checked_add, not saturating_add: silently clamping at u64::MAX would
    // hide a broken reward calculation instead of surfacing it.
    profile.total_steps = profile
        .total_steps
        .checked_add(steps_walked)
        .ok_or(GremlinError::MathOverflow)?;
    profile.total_elevation_m = profile
        .total_elevation_m
        .checked_add(elevation_gain_m)
        .ok_or(GremlinError::MathOverflow)?;
    profile.completed_trails_count = profile
        .completed_trails_count
        .checked_add(1)
        .ok_or(GremlinError::MathOverflow)?;
    profile.attestation_nonce = profile
        .attestation_nonce
        .checked_add(1)
        .ok_or(GremlinError::MathOverflow)?;

    msg!(
        "Adventure recorded for {}: +{} steps, +{} m elevation",
        ctx.accounts.owner.key(),
        steps_walked,
        elevation_gain_m
    );
    Ok(())
}
