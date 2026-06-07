"""Part candidate simulation orchestration."""

from __future__ import annotations

from digital_twin_lab.parts import PartValidationService
from digital_twin_lab.parts.fea_model import run_fea
from digital_twin_lab.utils.catalog import Catalog
from digital_twin_lab.utils.errors import ResourceNotFoundError, ValidationError


class PartSimulationService:
    def __init__(self, validator: PartValidationService | None = None, catalog: Catalog | None = None) -> None:
        self._validator = validator or PartValidationService()
        self._catalog = catalog or Catalog()

    def simulate_part_candidate(self, **kwargs) -> dict[str, object]:
        return self._validator.simulate(**kwargs)

    def run_fea(
        self,
        *,
        material: str,
        section: dict[str, object],
        loads: dict[str, float],
        operating_temp_c: float = 20.0,
        target_safety_factor: float = 1.5,
    ) -> dict[str, object]:
        """FEM/FEA structural check of a candidate part (Spec §8.3)."""
        try:
            return run_fea(
                material, section, loads,
                operating_temp_c=operating_temp_c,
                target_safety_factor=target_safety_factor,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def get_part(self, part_id: str) -> dict[str, object]:
        try:
            return self._catalog.load("part_models", f"{part_id}.yaml")
        except ResourceNotFoundError as error:
            raise ResourceNotFoundError(f"Part not found: {part_id}") from error
