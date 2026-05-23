from __future__ import annotations

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
        stability_bias = float(circuit_profile["stability_bias"])

        baseline_front = float(baseline_setup.get("front_rebound", 8))
        proposed_front = float(proposed_setup.get("front_rebound", baseline_front))
        baseline_rear = float(baseline_setup.get("rear_rebound", 10))
        proposed_rear = float(proposed_setup.get("rear_rebound", baseline_rear))
        baseline_height = float(baseline_setup.get("rear_ride_height_mm", 45))
        proposed_height = float(proposed_setup.get("rear_ride_height_mm", baseline_height))

        baseline_stability = round(stability_bias + baseline_front * 0.012 + baseline_rear * 0.014 - baseline_height * 0.002, 3)
        proposed_stability = round(stability_bias + proposed_front * 0.012 + proposed_rear * 0.014 - proposed_height * 0.002, 3)

        baseline_temp = round(ambient_temp_c * 0.35 + track_temp_c * 0.95 + thermal_load * 8.0, 3)
        temp_adjustment = (
            (proposed_front - baseline_front) * -0.35
            + (proposed_rear - baseline_rear) * -0.55
            + (proposed_height - baseline_height) * 0.18
            + (-1.8 if proposed_setup.get("engine_map") == "mapping_2" else 0.0)
        )
        proposed_temp = round(baseline_temp + temp_adjustment, 3)

        baseline_lap = round(base_lap + laps * 0.002 + thermal_load * 0.05 - baseline_stability * 0.08, 3)
        lap_gain = (
            (proposed_front - baseline_front) * -0.018
            + (proposed_rear - baseline_rear) * -0.024
            + (proposed_height - baseline_height) * 0.004
            + (-0.045 if proposed_setup.get("engine_map") == "mapping_2" else 0.0)
        )
        proposed_lap = round(baseline_lap + lap_gain, 3)

        baseline_metrics = {
            "lap_time_s": baseline_lap,
            "stability_score": baseline_stability,
            "rear_temp_c": baseline_temp,
        }
        proposed_metrics = {
            "lap_time_s": proposed_lap,
            "stability_score": proposed_stability,
            "rear_temp_c": proposed_temp,
        }
        delta_metrics = {
            "lap_time_delta_s": round(proposed_lap - baseline_lap, 3),
            "stability_score_delta": round(proposed_stability - baseline_stability, 3),
            "rear_temp_delta_c": round(proposed_temp - baseline_temp, 3),
        }
        return baseline_metrics, proposed_metrics, delta_metrics, diff
