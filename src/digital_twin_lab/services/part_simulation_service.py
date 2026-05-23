"""Part candidate simulation orchestration."""

from __future__ import annotations

from digital_twin_lab.parts import PartValidationService
from digital_twin_lab.utils.catalog import Catalog
from digital_twin_lab.utils.errors import ResourceNotFoundError


class PartSimulationService:
    def __init__(self, validator: PartValidationService | None = None, catalog: Catalog | None = None) -> None:
        self._validator = validator or PartValidationService()
        self._catalog = catalog or Catalog()

    def simulate_part_candidate(self, **kwargs) -> dict[str, object]:
        return self._validator.simulate(**kwargs)

    def get_part(self, part_id: str) -> dict[str, object]:
        try:
            return self._catalog.load("part_models", f"{part_id}.yaml")
        except ResourceNotFoundError as error:
            raise ResourceNotFoundError(f"Part not found: {part_id}") from error
