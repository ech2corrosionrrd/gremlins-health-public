"""
SIMULATION ONLY - this module does not touch Solana.

It fabricates plausible-looking asset ids, transaction hashes and Arweave
URIs so the rest of the stack can be developed end to end. Nothing produced
here exists on any cluster, and none of these hashes can be resolved by an
explorer or a DAS indexer.

Replacing it with a real implementation means:
  * creating a Bubblegum Merkle tree (spl-account-compression),
  * minting via mpl-bubblegum from a backend fee-payer (gasless relayer),
  * uploading metadata to Arweave/Irys and using the returned URI,
  * reading assets back through the Helius DAS API.

Until that exists, NFTMetadata.is_onchain stays False and no UI may present
these values as on-chain proof.
"""
import hashlib
import uuid
from typing import Any, Dict

# Imported by callers that want to label simulated output in responses/logs.
IS_SIMULATION = True


class MockSolanaService:
    @staticmethod
    def simulate_mint_compressed_nft(
        creator_wallet: str,
        title: str,
        rendered_art_url: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Returns fake but deterministic on-chain identifiers.

        Deterministic on purpose: the same activity re-minted in development
        yields the same ids, which keeps fixtures stable.
        """
        asset_seed = hashlib.sha256(
            f"{creator_wallet}{title}{rendered_art_url}".encode()
        ).hexdigest()
        return {
            # "sim_" prefixes make it obvious in a database dump that these
            # are not real Solana identifiers.
            "solana_asset_id": f"sim_cNFT_{asset_seed[:32]}",
            "mint_tx_hash": f"sim_tx_{hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:44]}",
            "arweave_metadata_uri": f"https://example.invalid/simulated/{asset_seed[:43]}",
            "is_simulation": "true",
        }
