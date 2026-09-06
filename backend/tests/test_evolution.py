import pytest
from app.services.evolution_service import EvolutionService
from app.models.gremlin import BiomeType, GremlinRarity


def test_biome_detection_mountain():
    biome = EvolutionService.detect_biome(
        max_elevation_m=1850.0,
        temperature_c=12.0,
        weather_condition="sunny"
    )
    assert biome == BiomeType.MOUNTAIN_FROST.value


def test_biome_detection_storm():
    biome = EvolutionService.detect_biome(
        max_elevation_m=500.0,
        temperature_c=15.0,
        weather_condition="thunderstorm"
    )
    assert biome == BiomeType.STORMBRINGER.value


def test_evolution_level_and_rarity_progression():
    # Starting at Level 1 with 3500 XP
    new_lvl, rem_xp, next_xp, rarity, traits = EvolutionService.apply_evolution_check(
        current_level=1,
        current_xp=3500,
        next_level_xp=1000,
        biome_affinity=BiomeType.MOUNTAIN_FROST.value
    )
    
    assert new_lvl >= 3
    assert rarity == GremlinRarity.UNCOMMON.value
    assert traits["horns"] == "ice_crystals"
    assert traits["skin"] == BiomeType.MOUNTAIN_FROST.value


def test_stamina_and_xp_calculation():
    stamina, xp, bonus = EvolutionService.calculate_rewards(
        total_steps=15000,
        elevation_gain_m=600.0,
        detected_biome=BiomeType.MOUNTAIN_FROST.value,
        verification_score=95.0
    )
    
    assert stamina >= 70
    assert xp >= 2500
    assert bonus == 1.25 # +25% Biome bonus
