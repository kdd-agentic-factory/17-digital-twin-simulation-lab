from __future__ import annotations

from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.simulation.result_builder import EngineSimulationResult
from digital_twin_lab.simulation.simulation_engine import SimulationEngine


class ScenarioRunner:
    """Runs a scenario through the spec-aligned simulation engine."""

    def __init__(self, engine: SimulationEngine | None = None) -> None:
        self._engine = engine or SimulationEngine()

    def run(self, scenario: SimulationScenario, *, iterations: int = 1) -> EngineSimulationResult:
        return self._engine.run(scenario, iterations=iterations)
