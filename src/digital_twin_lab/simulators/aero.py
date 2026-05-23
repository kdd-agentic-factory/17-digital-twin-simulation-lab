AERO_PACKAGES = {
    "baseline": {"balance_delta_pct": 0.0, "temp_delta_c": 0.0, "lap_penalty_s": 0.0},
    "high_downforce": {"balance_delta_pct": -1.8, "temp_delta_c": -0.6, "lap_penalty_s": 0.03},
    "low_drag": {"balance_delta_pct": 1.2, "temp_delta_c": 0.4, "lap_penalty_s": -0.02},
    "front_stability": {"balance_delta_pct": -1.0, "temp_delta_c": -0.2, "lap_penalty_s": 0.01},
}


def aero_balance_effect(package_name: str) -> dict[str, float]:
    return AERO_PACKAGES.get(package_name, AERO_PACKAGES["baseline"])
