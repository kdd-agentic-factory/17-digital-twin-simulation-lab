from __future__ import annotations


class EngineMapModel:
    """Maps engine-map identifiers to simple torque and thermal effects."""

    _MAP_FACTORS = {
        "mapping_1": {"torque_factor": 1.0, "thermal_delta_c": 0.0},
        "mapping_2": {"torque_factor": 1.04, "thermal_delta_c": -1.8},
        "mapping_3": {"torque_factor": 0.97, "thermal_delta_c": -3.0},
    }

    def get_map(self, engine_map: str) -> dict[str, float]:
        return self._MAP_FACTORS.get(engine_map, self._MAP_FACTORS["mapping_1"])
