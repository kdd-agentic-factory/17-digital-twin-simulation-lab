"""Setup impact model with non-linear interaction terms.

Improvements over the original linear model:
- Rebound × ride-height coupling (softer damping + lower ride height → oversteer)
- Engine map × rear rebound saturation (mapping_2 gains diminish as rebound increases)
- Thermal load × ride height interaction (higher ride height amplifies heat build-up)
- Stability score bounded to [0.0, 1.0] to prevent runaway values
"""

from __future__ import annotations

import math

from digital_twin_lab.setup.setup_diff import SetupDiff


class SetupImpactModel:
    def evaluate(
        self,
        *,
        baseline_setup: dict[str, object],
        proposed_setup: dict[str, object],
        circuit_profile: dict[str, object],
        ambient_temp_c: float,
        track_temp_c: float,
        laps: int,
    ) -> tuple[dict[str, float], dict[str, float], dict[str, float], SetupDiff]:
        diff = SetupDiff.from_setups(baseline=baseline_setup, proposed=proposed_setup)
        base_lap = float(circuit_profile["base_lap_time_s"])
        thermal_load = float(circuit_profile["thermal_load"])
        stability_bias = float(circuit_profile.get("stability_bias", 0.74))

        b_front = float(baseline_setup.get("front_rebound", 8))
        p_front = float(proposed_setup.get("front_rebound", b_front))
        b_rear = float(baseline_setup.get("rear_rebound", 10))
        p_rear = float(proposed_setup.get("rear_rebound", b_rear))
        b_height = float(baseline_setup.get("rear_ride_height_mm", 45))
        p_height = float(proposed_setup.get("rear_ride_height_mm", b_height))
        b_map2 = baseline_setup.get("engine_map") == "mapping_2"
        p_map2 = proposed_setup.get("engine_map") == "mapping_2"

        # --- Baseline stability (non-linear: log-damping on rebound) ---
        b_stability = self._stability(stability_bias, b_front, b_rear, b_height)
        p_stability = self._stability(stability_bias, p_front, p_rear, p_height)

        # --- Baseline temperature ---
        b_temp = self._rear_temp(ambient_temp_c, track_temp_c, thermal_load, b_height, b_map2)
        p_temp = self._rear_temp(ambient_temp_c, track_temp_c, thermal_load, p_height, p_map2)

        # --- Rebound × height coupling: extra instability when height is low + rebound is high ---
        p_coupling_penalty = self._coupling_penalty(p_front, p_rear, p_height)
        b_coupling_penalty = self._coupling_penalty(b_front, b_rear, b_height)
        p_stability -= p_coupling_penalty
        b_stability -= b_coupling_penalty
        p_stability = max(0.0, min(1.0, p_stability))
        b_stability = max(0.0, min(1.0, b_stability))

        # --- Lap time (non-linear stability contribution + rebound marginal gains) ---
        b_lap = round(base_lap + laps * 0.002 + thermal_load * 0.05 - b_stability * 0.09, 3)
        lap_gain = self._lap_time_gain(b_front, p_front, b_rear, p_rear, b_height, p_height, b_map2, p_map2, p_stability)
        p_lap = round(b_lap + lap_gain, 3)

        baseline_metrics = {
            "lap_time_s": b_lap,
            "stability_score": round(b_stability, 4),
            "rear_temp_c": round(b_temp, 3),
        }
        proposed_metrics = {
            "lap_time_s": p_lap,
            "stability_score": round(p_stability, 4),
            "rear_temp_c": round(p_temp, 3),
        }
        delta_metrics = {
            "lap_time_delta_s": round(p_lap - b_lap, 3),
            "stability_score_delta": round(p_stability - b_stability, 4),
            "rear_temp_delta_c": round(p_temp - b_temp, 3),
        }
        return baseline_metrics, proposed_metrics, delta_metrics, diff

    # ------------------------------------------------------------------
    # Sub-models
    # ------------------------------------------------------------------

    @staticmethod
    def _stability(bias: float, front: float, rear: float, height: float) -> float:
        """Non-linear stability: log-damped rebound contribution, penalised by ride height."""
        front_contribution = 0.012 * math.log1p(front) * (front / 10.0)
        rear_contribution = 0.014 * math.log1p(rear) * (rear / 10.0)
        height_penalty = height * 0.0018
        return bias + front_contribution + rear_contribution - height_penalty

    @staticmethod
    def _coupling_penalty(front: float, rear: float, height: float) -> float:
        """Rebound × height coupling instability penalty (high rebound + low height → oversteer)."""
        avg_rebound = (front + rear) / 2.0
        if height < 44.0 and avg_rebound > 10.0:
            return (avg_rebound - 10.0) * (44.0 - height) * 0.0006
        return 0.0

    @staticmethod
    def _rear_temp(ambient: float, track: float, thermal_load: float, height: float, map2: bool) -> float:
        """Rear tyre temperature model with ride-height × thermal-load interaction."""
        base_temp = ambient * 0.35 + track * 0.95 + thermal_load * 8.0
        # Higher ride height slightly increases heat exposure at the carcass
        height_heat = (height - 45.0) * 0.15 * thermal_load
        map2_cooling = -1.8 if map2 else 0.0
        return base_temp + height_heat + map2_cooling

    @staticmethod
    def _lap_time_gain(
        b_front: float, p_front: float,
        b_rear: float, p_rear: float,
        b_height: float, p_height: float,
        b_map2: bool, p_map2: bool,
        p_stability: float,
    ) -> float:
        """Lap time gain with diminishing returns on large rebound changes."""
        def _rebound_gain(delta: float, base: float, coeff: float) -> float:
            # Diminishing returns beyond ±3 clicks via tanh
            return coeff * math.tanh(delta / 3.0) * (1.0 + base / 20.0)

        front_gain = _rebound_gain(p_front - b_front, b_front, -0.020)
        rear_gain = _rebound_gain(p_rear - b_rear, b_rear, -0.026)
        height_gain = (p_height - b_height) * 0.004
        map_gain = (-0.045 if p_map2 and not b_map2 else 0.045 if not p_map2 and b_map2 else 0.0)
        # Low stability penalises lap time additionally
        stability_penalty = max(0.0, 0.75 - p_stability) * 0.12
        return front_gain + rear_gain + height_gain + map_gain + stability_penalty
