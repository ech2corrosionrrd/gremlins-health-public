import math
import statistics
from typing import List, Tuple, Optional
from app.core.config import settings
from app.schemas.activity import TelemetryDataPoint

# Below this many steps the cadence statistics are meaningless.
MIN_STEPS_FOR_FULL_ANALYSIS = 100
# Score granted to a session too short to analyse. Kept low so that splitting
# a fake walk into many tiny uploads earns less, not more, than one real one.
LOW_SIGNAL_SCORE = 55.0


class AntiCheatService:
    @staticmethod
    def calculate_cadence_variance(samples: List[TelemetryDataPoint]) -> float:
        """
        Human walking/running naturally has non-uniform micro-intervals (cadence variance).
        Mechanical shakers or software loops generate synthetic uniform frequencies (variance ~ 0.0).
        """
        if not samples or len(samples) < 5:
            return 0.15 # Default healthy human variance for short sessions
        
        cadence_values = [s.cadence_spm for s in samples if s.cadence_spm > 0]
        if not cadence_values or len(cadence_values) < 5:
            return 0.05
        
        # Coefficient of variation = std_dev / mean
        mean_cadence = float(statistics.mean(cadence_values))
        std_cadence = float(statistics.stdev(cadence_values)) if len(cadence_values) > 1 else 0.0
        
        if mean_cadence == 0:
            return 0.0
            
        cv = std_cadence / mean_cadence
        return round(cv, 4)

    @staticmethod
    def verify_speed_and_elevation(
        samples: List[TelemetryDataPoint],
        elevation_gain_m: float,
        duration_seconds: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks for vehicle spoofing (unrealistic human speed) and impossible elevation jumps.
        """
        if not samples:
            return True, None
            
        max_speed = max((s.speed_kmh for s in samples), default=0.0)
        if max_speed > settings.MAX_HUMAN_SPEED_KMH:
            return False, f"Detected vehicle speed ({max_speed:.1f} km/h > max human sprint limit)"
        
        # Check impossible vertical climb speed (> 1500 meters per hour continuous is impossible for humans)
        if duration_seconds > 0:
            vertical_speed_m_per_hour = (elevation_gain_m / duration_seconds) * 3600
            if vertical_speed_m_per_hour > 2200.0:
                return False, f"Impossible vertical climb rate ({vertical_speed_m_per_hour:.0f} m/h)"
                
        return True, None

    @classmethod
    def evaluate_activity(
        cls,
        total_steps: int,
        duration_seconds: int,
        elevation_gain_m: float,
        telemetry_samples: List[TelemetryDataPoint],
        device_integrity_token: Optional[str],
        ble_pack_count: int
    ) -> Tuple[bool, float, float, Optional[str]]:
        """
        Returns: (is_verified, verification_score [0..100], cadence_variance, flagged_reason)
        """
        # Very short sessions carry too little signal for the statistical
        # checks below, so they are accepted - but at a reduced score rather
        # than a perfect one. Previously this returned 100.0 and skipped every
        # check, which let an attacker farm unlimited credit in <100-step
        # batches.
        if total_steps < MIN_STEPS_FOR_FULL_ANALYSIS:
            variance = cls.calculate_cadence_variance(telemetry_samples)
            speed_ok, speed_err = cls.verify_speed_and_elevation(
                telemetry_samples, elevation_gain_m, duration_seconds
            )
            if not speed_ok:
                return False, 10.0, variance, speed_err
            return True, LOW_SIGNAL_SCORE, variance, None

        # 1. Step Rate Plausibility (Cannot exceed 240 steps/min sustained)
        if duration_seconds > 0:
            avg_spm = (total_steps / duration_seconds) * 60
            if avg_spm > settings.MAX_HUMAN_CADENCE_SPM:
                return False, 15.0, 0.01, f"Step frequency too high ({avg_spm:.1f} SPM)"

        # 2. Cadence Variance Check
        variance = cls.calculate_cadence_variance(telemetry_samples)
        if telemetry_samples and len(telemetry_samples) >= 10:
            if variance < settings.MIN_STEP_CADENCE_VARIANCE:
                return False, 25.0, variance, f"Cadence uniformity anomaly ({variance:.4f} < threshold). Likely mechanical shaker."

        # 3. Speed & Physics validation
        speed_ok, speed_err = cls.verify_speed_and_elevation(
            telemetry_samples, elevation_gain_m, duration_seconds
        )
        if not speed_ok:
            return False, 10.0, variance, speed_err

        # 4. Score Calculation
        score = 80.0
        
        # Hardware integrity bonus
        if device_integrity_token and len(device_integrity_token) > 16:
            score += 10.0
            
        # Proof of Pack (BLE mesh) bonus
        if ble_pack_count > 0:
            score += min(10.0, ble_pack_count * 5.0)

        score = min(100.0, score)
        return True, score, variance, None
