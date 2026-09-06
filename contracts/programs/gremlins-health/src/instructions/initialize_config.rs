use anchor_lang::prelude::*;

use crate::errors::GremlinError;
use crate::state::ProgramConfig;

/// One-time setup: records the admin and the backend oracle key that every
/// progression instruction checks against.
#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(
        init,
        payer = admin,
        space = ProgramConfig::LEN,
        seeds = [ProgramConfig::SEED],
        bump
    )]
    pub config: Account<'info, ProgramConfig>,

    #[account(mut)]
    pub admin: Signer<'info>,

    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<InitializeConfig>, oracle_authority: Pubkey) -> Result<()> {
    require!(
        oracle_authority != Pubkey::default(),
        GremlinError::InvalidOracleAuthority
    );

    let config = &mut ctx.accounts.config;
    config.admin = ctx.accounts.admin.key();
    config.oracle_authority = oracle_authority;
    config.bump = ctx.bumps.config;

    msg!("Config initialized. Oracle authority: {}", oracle_authority);
    Ok(())
}

/// Lets the admin rotate the oracle key - the recovery path if the backend
/// signer is ever compromised.
#[derive(Accounts)]
pub struct SetOracleAuthority<'info> {
    #[account(
        mut,
        seeds = [ProgramConfig::SEED],
        bump = config.bump,
        has_one = admin @ GremlinError::UnauthorizedAdmin,
    )]
    pub config: Account<'info, ProgramConfig>,

    pub admin: Signer<'info>,
}

pub fn set_oracle_authority(
    ctx: Context<SetOracleAuthority>,
    new_oracle_authority: Pubkey,
) -> Result<()> {
    require!(
        new_oracle_authority != Pubkey::default(),
        GremlinError::InvalidOracleAuthority
    );

    ctx.accounts.config.oracle_authority = new_oracle_authority;
    msg!("Oracle authority rotated to {}", new_oracle_authority);
    Ok(())
}
