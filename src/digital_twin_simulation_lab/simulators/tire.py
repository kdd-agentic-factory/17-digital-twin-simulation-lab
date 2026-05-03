def tire_pressure_effect(rear_pressure_delta_bar: float) -> dict[str, float]:
    bounded_delta = max(-0.25, min(0.25, rear_pressure_delta_bar))
    return {
        "temp_delta_c": 7.0 * bounded_delta,
        "spin_delta_pct": 4.0 * bounded_delta,
        "lap_penalty_s": abs(bounded_delta) * 0.08,
    }


def degradation_delay_laps(temp_delta_c: float, spin_delta_pct: float) -> int:
    cooling_gain = max(0.0, -temp_delta_c) / 1.5
    traction_gain = max(0.0, -spin_delta_pct) / 4.0
    return round(min(5.0, cooling_gain + traction_gain))
