use anchor_lang::prelude::*;

#[error_code]
pub enum GremlinError {
    #[msg("Insufficient XP threshold required for this evolution tier.")]
    InsufficientXpForEvolution,

    #[msg("Gremlin is already at maximum level.")]
    MaxLevelReached,

    #[msg("Unauthorized: caller is not the legitimate owner of this Gremlin.")]
    UnauthorizedGremlinOwner,

    #[msg("Unauthorized: caller is not the program admin.")]
    UnauthorizedAdmin,

    #[msg("Invalid telemetry attestation: signer is not the configured oracle.")]
    InvalidTelemetryProof,

    #[msg("Attestation nonce does not match the profile; possible replay.")]
    StaleAttestation,

    #[msg("Trait value is outside the permitted range.")]
    InvalidTraitValue,

    #[msg("Oracle authority must not be the default pubkey.")]
    InvalidOracleAuthority,

    #[msg("Mathematical overflow occurred during reward calculation.")]
    MathOverflow,
}
