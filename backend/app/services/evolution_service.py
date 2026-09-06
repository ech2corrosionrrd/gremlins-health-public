import math
from typing import Tuple, Dict, Any
from app.models.gremlin import BiomeType, GremlinRarity


class EvolutionService:
    @staticmethod
    def detect_biome(
        max_elevation_m: float,
        temperature_c: float,
        weather_condition: str,
        time_hour: int = 12
    ) -> str:
        """
        Calculates the biome affinity based on telemetry environment.
        """
        # 1. Mountain Frost (> 1400m altitude or freezing temps)
        if max_elevation_m >= 1400.0 or temperature_c <= 0.0:
            return BiomeType.MOUNTAIN_FROST.value
            
        # 2. Extreme Storm (Thunderstorm, blizzard, gale)
        if weather_condition.lower() in ["storm", "thunderstorm", "blizzard", "heavy_rain"]:
            return BiomeType.STORMBRINGER.value
            
        # 3. Cyber Shadow (Night city walks)
        if (time_hour >= 22 or time_hour <= 5) and max_elevation_m < 300.0:
            return BiomeType.CYBER_SHADOW.value
            
        # 4. Forest Guardian (High green canopy elevation 400m - 1400m)
        if 400.0 <= max_elevation_m < 1400.0:
            return BiomeType.FOREST_GUARDIAN.value
            
        return BiomeType.COMMON.value

    @staticmethod
    def calculate_rewards(
        total_steps: int,
        elevation_gain_m: float,
        detected_biome: str,
        verification_score: float
    ) -> Tuple[int, int, float]:
        """
        Returns: (stamina_earned, gremlin_xp_gained, biome_resonance_bonus)
        """
        quality_multiplier = verification_score / 100.0
        
        # Stamina formula: 1 Stamina per 200 steps
        base_stamina = int((total_steps / 200) * quality_multiplier)
        
        # XP formula: 1 XP per 10 steps + 2 XP per vertical meter
        base_xp = int(((total_steps / 10) + (elevation_gain_m * 2.0)) * quality_multiplier)
        
        # Biome Resonance Multiplier
        biome_multiplier = 1.0
        if detected_biome != BiomeType.COMMON.value:
            biome_multiplier = 1.25 # +25% XP bonus in specialized biomes
            
        total_xp = int(base_xp * biome_multiplier)
        return max(5, base_stamina), max(10, total_xp), biome_multiplier

    @staticmethod
    def apply_evolution_check(
        current_level: int,
        current_xp: int,
        next_level_xp: int,
        biome_affinity: str
    ) -> Tuple[int, int, int, str, Dict[str, Any]]:
        """
        Evaluates level-up thresholds and morphological traits evolution.
        Returns: (new_level, remaining_xp, new_next_level_xp, new_rarity, new_traits)
        """
        new_level = current_level
        xp = current_xp
        next_xp = next_level_xp
        
        while xp >= next_xp:
            xp -= next_xp
            new_level += 1
            next_xp = int(next_xp * 1.5)
            
        # Determine Rarity Tier
        if new_level >= 25:
            rarity = GremlinRarity.LEGENDARY.value
        elif new_level >= 15:
            rarity = GremlinRarity.EPIC.value
        elif new_level >= 8:
            rarity = GremlinRarity.RARE.value
        elif new_level >= 3:
            rarity = GremlinRarity.UNCOMMON.value
        else:
            rarity = GremlinRarity.COMMON.value

        # Evolve visual traits based on Biome & Level
        traits = {
            "horns": "none" if new_level < 3 else ("ice_crystals" if biome_affinity == BiomeType.MOUNTAIN_FROST.value else "leaf_horns"),
            "wings": "none" if new_level < 8 else ("storm_sparks" if biome_affinity == BiomeType.STORMBRINGER.value else "feathered"),
            "aura": "none" if new_level < 15 else ("neon_glow" if biome_affinity == BiomeType.CYBER_SHADOW.value else "cosmic_mist"),
            "skin": biome_affinity
        }
        
        return new_level, xp, next_xp, rarity, traits
