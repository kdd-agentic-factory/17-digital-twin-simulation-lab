"""Scenario orchestration services."""

from __future__ import annotations

from typing import Any

from digital_twin_lab.models.part import PartCandidate
from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.models.setup import SetupChange
from digital_twin_lab.utils.errors import ResourceNotFoundError


class ScenarioService:
    """Builds and mutates scenario models for service consumers."""

    _CATALOG: tuple[dict[str, Any], ...] = (
        {
            "scenario_id": "jerez-map2-rebound",
            "name": "Jerez mapping 2 rear rebound study",
            "scenario_type": "setup_change",
            "circuit_id": "jerez",
            "session_id": "race",
            "baseline_setup_id": "jerez-baseline",
            "lap_range": (1, 12),
            "assumptions": ["Deterministic MVP heuristics", "Stable rider adaptation"],
            "metadata": {
                "proposed_setup": {
                    "front_rebound": 9,
                    "rear_rebound": 11,
                    "rear_ride_height_mm": 47,
                    "engine_map": "mapping_2",
                },
                "ambient_temp_c": 31.0,
                "track_temp_c": 41.0,
                "laps": 12,
            },
        },
        {
            "scenario_id": "mugello-balance-window",
            "name": "Mugello stability preservation window",
            "scenario_type": "setup_change",
            "circuit_id": "mugello",
            "session_id": "fp2",
            "baseline_setup_id": "mugello-baseline",
            "lap_range": (3, 10),
            "assumptions": ["Dry track", "Nominal aero balance"],
            "metadata": {
                "proposed_setup": {
                    "front_rebound": 8,
                    "rear_rebound": 10,
                    "rear_ride_height_mm": 46,
                    "engine_map": "mapping_1",
                },
                "ambient_temp_c": 28.0,
                "track_temp_c": 38.0,
                "laps": 8,
            },
        },
    )

    def create_scenario(
        self,
        *,
        scenario_id: str,
        name: str,
        scenario_type: str,
        circuit_id: str,
        session_id: str,
        baseline_setup_id: str,
        lap_range: tuple[int, int],
        description: str | None = None,
        setup_change: SetupChange | None = None,
        part_candidate: PartCandidate | None = None,
        tire_model_id: str | None = None,
        corner_ids: list[str] | None = None,
        assumptions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SimulationScenario:
        """Create a validated simulation scenario model."""
        scenario_metadata = dict(metadata or {})
        if description:
            scenario_metadata.setdefault("description", description)

        return SimulationScenario(
            scenario_id=scenario_id,
            name=name,
            scenario_type=scenario_type,
            circuit_id=circuit_id,
            session_id=session_id,
            baseline_setup_id=baseline_setup_id,
            setup_change=setup_change,
            part_candidate=part_candidate,
            tire_model_id=tire_model_id,
            lap_range=lap_range,
            corner_ids=corner_ids or [],
            assumptions=assumptions or [],
            metadata=scenario_metadata,
        )

    def attach_setup_change(
        self,
        scenario: SimulationScenario,
        setup_change: SetupChange,
    ) -> SimulationScenario:
        """Return a copy of the scenario with a setup change applied."""
        return scenario.model_copy(update={"setup_change": setup_change})

    def attach_part_candidate(
        self,
        scenario: SimulationScenario,
        part_candidate: PartCandidate,
    ) -> SimulationScenario:
        """Return a copy of the scenario with a part candidate applied."""
        return scenario.model_copy(update={"part_candidate": part_candidate})

    def clone_scenario(
        self,
        scenario: SimulationScenario,
        *,
        scenario_id: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SimulationScenario:
        """Clone a scenario with a new identifier and optional metadata overrides."""
        merged_metadata = {**scenario.metadata, **(metadata or {})}
        return scenario.model_copy(
            update={
                "scenario_id": scenario_id,
                "name": name or scenario.name,
                "metadata": merged_metadata,
            }
        )

    def summarize(self, scenario: SimulationScenario) -> dict[str, Any]:
        """Create an API-friendly summary payload for a scenario."""
        return {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "type": scenario.scenario_type,
            "circuit_id": scenario.circuit_id,
            "session_id": scenario.session_id,
            "lap_range": scenario.lap_range,
            "has_setup_change": scenario.setup_change is not None,
            "has_part_candidate": scenario.part_candidate is not None,
            "corner_count": len(scenario.corner_ids),
            "assumptions": list(scenario.assumptions),
        }

    def list_scenarios(self) -> list[dict[str, Any]]:
        return [self.summarize(self._from_catalog(item)) for item in self._CATALOG]

    def get_scenario(self, scenario_id: str) -> SimulationScenario:
        for item in self._CATALOG:
            if item["scenario_id"] == scenario_id:
                return self._from_catalog(item)
        raise ResourceNotFoundError(f"Scenario not found: {scenario_id}")

    def _from_catalog(self, item: dict[str, Any]) -> SimulationScenario:
        return self.create_scenario(
            scenario_id=item["scenario_id"],
            name=item["name"],
            scenario_type=item["scenario_type"],
            circuit_id=item["circuit_id"],
            session_id=item["session_id"],
            baseline_setup_id=item["baseline_setup_id"],
            lap_range=item["lap_range"],
            assumptions=item.get("assumptions"),
            metadata=item.get("metadata"),
        )
