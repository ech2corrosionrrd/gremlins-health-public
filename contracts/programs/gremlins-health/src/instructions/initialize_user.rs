use anchor_lang::prelude::*;
use crate::state::{GremlinAccount, UserProfile};

#[derive(Accounts)]
pub struct InitializeUser<'info> {
    #[account(
        init,
        payer = authority,
        space = UserProfile::LEN,
        seeds = [UserProfile::SEED, authority.key().as_ref()],
        bump
    )]
    pub user_profile: Account<'info, UserProfile>,

    #[account(
        init,
        payer = authority,
        space = GremlinAccount::LEN,
        seeds = [GremlinAccount::SEED, authority.key().as_ref()],
        bump
    )]
    pub gremlin_account: Account<'info, GremlinAccount>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<InitializeUser>) -> Result<()> {
    let user_profile = &mut ctx.accounts.user_profile;
    user_profile.authority = ctx.accounts.authority.key();
    user_profile.reputation_score = 100;
    user_profile.total_steps = 0;
    user_profile.total_elevation_m = 0;
    user_profile.completed_trails_count = 0;
    user_profile.streak_days = 1;
    user_profile.attestation_nonce = 0;
    user_profile.bump = ctx.bumps.user_profile;

    let gremlin = &mut ctx.accounts.gremlin_account;
    gremlin.owner = ctx.accounts.authority.key();
    gremlin.level = 1;
    gremlin.rarity = 0; // Common
    gremlin.biome_affinity = 0; // Common
    gremlin.total_xp = 0;
    gremlin.last_evolved_ts = Clock::get()?.unix_timestamp;
    gremlin.bump = ctx.bumps.gremlin_account;

    msg!("Gremlin Health: User Profile & Starter Gremlin initialized for {}", ctx.accounts.authority.key());
    Ok(())
}
