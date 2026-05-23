from __future__ import annotations


class AeroPartModel:
    def simulate(self, *, part_model: dict[str, object], circuit_profile: dict[str, object]) -> dict[str, float]:
        straight_bias = float(circuit_profile["straight_bias"])
        stability_bias = float(circuit_profile["stability_bias"])
        return {
            "top_speed_delta_kph": round(float(part_model.get("drag_gain_kph", 0.0)) * straight_bias, 3),
            "stability_delta": round(float(part_model.get("stability_delta", 0.0)) * (2.0 - stability_bias), 3),
            "rear_temp_delta_c": round(float(part_model.get("rear_temp_delta_c", 0.0)), 3),
        }
