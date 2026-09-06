use anchor_lang::prelude::*;

pub mod errors;
pub mod instructions;
pub mod state;

use instructions::*;

declare_id!("A9oXQuqhwkycQKPRAHTrqBYZ8v985PagPmcQvEWtSmEX");

#[program]
pub mod gremlins_health {
    use super::*;

    /// One-time setup. Must run before any progression instruction.
    pub fn initialize_config(
        ctx: Context<InitializeConfig>,
        oracle_authority: Pubkey,
    ) -> Result<()> {
        instructions::initialize_config::handler(ctx, oracle_authority)
    }

    /// Rotates the backend oracle key (admin only).
    pub fn set_oracle_authority(
        ctx: Context<SetOracleAuthority>,
        new_oracle_authority: Pubkey,
    ) -> Result<()> {
        instructions::initialize_config::set_oracle_authority(ctx, new_oracle_authority)
    }

    /// Creates the player's profile and starter Gremlin. Self-service: it
    /// grants no progression, so it needs no oracle signature.
    pub fn initialize_user(ctx: Context<InitializeUser>) -> Result<()> {
        instructions::initialize_user::handler(ctx)
    }

    /// Applies an oracle-attested evolution.
    pub fn evolve_gremlin(
        ctx: Context<EvolveGremlin>,
        expected_nonce: u64,
        new_level: u8,
        new_rarity: u8,
        new_biome_affinity: u8,
        gained_xp: u64,
    ) -> Result<()> {
        instructions::evolve_gremlin::handler(
            ctx,
            expected_nonce,
            new_level,
            new_rarity,
            new_biome_affinity,
            gained_xp,
        )
    }

    /// Records a verified adventure. NOTE: does not mint a cNFT - see
    /// instructions/mint_cnft.rs for what is still missing.
    pub fn record_adventure(
        ctx: Context<RecordAdventure>,
        expected_nonce: u64,
        steps_walked: u64,
        elevation_gain_m: u32,
        metadata_uri: String,
    ) -> Result<()> {
        instructions::mint_cnft::handler(
            ctx,
            expected_nonce,
            steps_walked,
            elevation_gain_m,
            metadata_uri,
        )
    }
}
