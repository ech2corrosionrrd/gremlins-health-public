"""
SIMULATION ONLY - no image is generated.

build_generation_prompt() is real and is what a worker would send to FLUX;
generate_artwork() only returns a URL-shaped string for a file that does not
exist. Swap in a RunPod/Replicate call plus real object storage before any of
this reaches users.
"""
import hashlib
from typing import Any, Dict

IS_SIMULATION = True


class MockAIRenderService:
    @staticmethod
    def build_generation_prompt(
        location_name: str,
        biome_type: str,
        rarity: str,
        elevation_m: float,
        weather: str
    ) -> str:
        """
        Synthesizes the precise FLUX/SDXL LoRA prompt for the Gremlin companion embedded in the landscape.
        """
        base_prompt = (
            f"masterpiece, highly detailed 3D digital art, cute mischievous fantasy creature gremlin companion "
            f"sitting peacefully on a scenic mountain viewpoint overlooking {location_name}. "
            f"Environment: {weather} conditions, {biome_type} biome elements, dramatic atmospheric lighting, "
            f"elevation {elevation_m:.0f}m, realistic depth of field, 8k resolution, Unreal Engine 5 render style, "
            f"tier: {rarity} glowing artifacts."
        )
        return base_prompt

    @classmethod
    def generate_artwork(
        cls,
        original_photo_url: str,
        location_name: str,
        biome_type: str,
        rarity: str,
        elevation_m: float,
        weather: str
    ) -> Dict[str, Any]:
        """
        Returns a placeholder artwork URL and Metaplex-style attributes.

        The URL points at a host that intentionally does not resolve, so a
        simulated asset can never be mistaken for a rendered one.
        """
        prompt = cls.build_generation_prompt(location_name, biome_type, rarity, elevation_m, weather)
        
        # Deterministic generation hash based on inputs
        hash_seed = hashlib.sha256(f"{original_photo_url}{location_name}{rarity}".encode()).hexdigest()[:12]
        
        # Rendered image URL (mocking dynamic CDN asset)
        rendered_url = (
            f"https://example.invalid/simulated-art/"
            f"{rarity.lower()}_{biome_type}_{hash_seed}.webp"
        )
        
        attributes = {
            "Location": location_name,
            "Biome": biome_type,
            "Rarity": rarity,
            "Elevation_m": elevation_m,
            "Weather": weather,
            "Prompt_Signature": hashlib.md5(prompt.encode()).hexdigest(),
            "Engine": "simulated (no model was run)"
        }
        
        return {
            "is_simulation": True,
            "rendered_art_url": rendered_url,
            "prompt_used": prompt,
            "attributes": attributes
        }
