import pytest
from app.services.anticheat_service import AntiCheatService
from app.schemas.activity import TelemetryDataPoint


def test_mechanical_shaker_detection():
    """
    Simulates a mechanical phone shaker that produces exact uniform cadence (120 SPM).
    Should fail with low cadence variance.
    """
    fake_samples = [
        TelemetryDataPoint(
            timestamp_ms=1000 * i,
            lat=48.1600,
            lng=24.5000,
            altitude_m=800.0,
            speed_kmh=0.0,
            cadence_spm=120 # Fixed uniform cadence
        )
        for i in range(20)
    ]
    
    is_valid, score, variance, flagged_reason = AntiCheatService.evaluate_activity(
        total_steps=2400,
        duration_seconds=1200,
        elevation_gain_m=0.0,
        telemetry_samples=fake_samples,
        device_integrity_token=None,
        ble_pack_count=0
    )
    
    assert is_valid is False
    assert variance < 0.04
    assert "uniformity anomaly" in flagged_reason.lower()


def test_legitimate_hiking_activity():
    """
    Simulates real human hiking with natural cadence variations (90-140 SPM) and elevation.
    Should pass with high verification score.
    """
    cadences = [95, 105, 115, 120, 110, 100, 130, 125, 90, 110, 118, 102, 112, 125, 135]
    real_samples = [
        TelemetryDataPoint(
            timestamp_ms=1000 * i * 30,
            lat=48.1600 + (i * 0.0002),
            lng=24.5000 + (i * 0.0002),
            altitude_m=1200.0 + (i * 15.0),
            speed_kmh=4.5,
            cadence_spm=cadences[i]
        )
        for i in range(len(cadences))
    ]
    
    is_valid, score, variance, flagged_reason = AntiCheatService.evaluate_activity(
        total_steps=1800,
        duration_seconds=450,
        elevation_gain_m=225.0,
        telemetry_samples=real_samples,
        device_integrity_token="valid_apple_device_check_token_123456789",
        ble_pack_count=2
    )
    
    assert is_valid is True
    assert score >= 90.0
    assert variance >= 0.04
    assert flagged_reason is None


def test_vehicle_speed_detection():
    """
    Simulates a player riding in a car (80 km/h).
    Should fail due to exceeding maximum human sprinting speed.
    """
    car_samples = [
        TelemetryDataPoint(
            timestamp_ms=1000 * i * 10,
            lat=48.1600 + (i * 0.01),
            lng=24.5000 + (i * 0.01),
            altitude_m=400.0,
            speed_kmh=75.0,
            cadence_spm=90 + (i * 5) # Varied cadence
        )
        for i in range(10)
    ]
    
    is_valid, score, variance, flagged_reason = AntiCheatService.evaluate_activity(
        total_steps=1100,
        duration_seconds=600,
        elevation_gain_m=10.0,
        telemetry_samples=car_samples,
        device_integrity_token=None,
        ble_pack_count=0
    )
    
    assert is_valid is False
    assert "vehicle speed" in flagged_reason.lower()
