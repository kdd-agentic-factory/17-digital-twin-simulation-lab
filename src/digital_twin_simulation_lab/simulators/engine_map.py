ENGINE_MAPS = {
    "baseline": {"torque_trim": 0.0, "thermal_trim_c": 0.0, "lap_penalty_s": 0.0},
    "mapping_1": {"torque_trim": 0.02, "thermal_trim_c": 1.2, "lap_penalty_s": -0.02},
    "mapping_2": {"torque_trim": -0.05, "thermal_trim_c": -2.1, "lap_penalty_s": 0.03},
    "mapping_3": {"torque_trim": -0.08, "thermal_trim_c": -3.0, "lap_penalty_s": 0.06},
}


def engine_map_effect(map_name: str) -> dict[str, float]:
    return ENGINE_MAPS.get(map_name, ENGINE_MAPS["baseline"])
