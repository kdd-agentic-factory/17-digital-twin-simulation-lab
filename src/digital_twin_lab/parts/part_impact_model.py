from __future__ import annotations

from digital_twin_lab.parts.aero_part_model import AeroPartModel
from digital_twin_lab.parts.cooling_part_model import CoolingPartModel


class PartImpactModel:
    def __init__(self) -> None:
        self._aero = AeroPartModel()
        self._cooling = CoolingPartModel()

    def evaluate(
        self,
        *,
        part_model: dict[str, object],
        circuit_profile: dict[str, object],
        ambient_temp_c: float,
        track_temp_c: float,
    ) -> dict[str, float]:
        part_type = str(part_model.get("type", "aero"))
        if part_type == "cooling":
            return self._cooling.simulate(part_model=part_model, track_temp_c=track_temp_c, ambient_temp_c=ambient_temp_c)
        return self._aero.simulate(part_model=part_model, circuit_profile=circuit_profile)
