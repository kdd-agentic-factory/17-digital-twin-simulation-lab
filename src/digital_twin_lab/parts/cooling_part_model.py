from __future__ import annotations


class CoolingPartModel:
    def simulate(self, *, part_model: dict[str, object], track_temp_c: float, ambient_temp_c: float) -> dict[str, float]:
        temperature_window_penalty = max(0.0, 32.0 - ambient_temp_c) * 0.18
        return {
            "top_speed_delta_kph": round(float(part_model.get("drag_gain_kph", 0.0)), 3),
            "stability_delta": round(float(part_model.get("stability_delta", 0.0)) - temperature_window_penalty * 0.01, 3),
            "rear_temp_delta_c": round(float(part_model.get("rear_temp_delta_c", 0.0)) - max(0.0, track_temp_c - 35.0) * 0.08, 3),
        }
