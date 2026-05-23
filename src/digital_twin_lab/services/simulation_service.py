"""Simulation orchestration services."""

from __future__ import annotations

from digital_twin_lab.models.risk import RiskClassification
from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.models.simulation import (
    SimulationRequest,
    SimulationResult,
    SimulationSummary,
)
from digital_twin_lab.services.scenario_service import ScenarioService
from digital_twin_lab.simulation.scenario_runner import ScenarioRunner


class SimulationService:
    """Coordinates model-based simulation requests over the engine layer."""

    _recent_results: list[SimulationResult] = []

    def __init__(self, scenario_runner: ScenarioRunner | None = None, scenario_service: ScenarioService | None = None) -> None:
        self._scenario_runner = scenario_runner or ScenarioRunner()
        self._scenario_service = scenario_service or ScenarioService()

    def run(self, request: SimulationRequest, scenario: SimulationScenario) -> SimulationResult:
        """Run a simulation request and adapt the engine output into API models."""
        engine_result = self._scenario_runner.run(scenario, iterations=request.iterations)
        risk = self._build_risk(engine_result)

        summary = SimulationSummary(
            spin_t05_delta_pct=engine_result.summary.spin_t05_delta_pct,
            rear_carcass_temp_delta_c=engine_result.summary.rear_carcass_temp_delta_c,
            lap_time_delta_s=engine_result.summary.lap_time_delta_s,
            degradation_delay_laps=engine_result.summary.degradation_delay_laps,
        )

        evidence = list(engine_result.evidence)
        evidence.append(f"Iterations requested: {request.iterations}.")
        if request.use_real_time_data:
            evidence.append("Real-time data flag enabled; placeholder mode used baseline metadata only.")

        result = SimulationResult(
            scenario_id=scenario.scenario_id,
            risk_classification=risk,
            summary=summary,
            recommendation=engine_result.recommendation,
            evidence=evidence,
            metadata={
                "iterations": request.iterations,
                "use_real_time_data": request.use_real_time_data,
                "scenario_type": scenario.scenario_type,
            },
        )
        self._remember_result(result)
        return result

    def list_simulations(self) -> list[dict[str, object]]:
        results = self._recent_results or [self.run(SimulationRequest(scenario_id=scenario.scenario_id), scenario) for scenario in [self._scenario_service.get_scenario("jerez-map2-rebound")]]
        return [result.model_dump(mode="json") for result in results]

    def latest_result(self) -> SimulationResult:
        if not self._recent_results:
            scenario = self._scenario_service.get_scenario("jerez-map2-rebound")
            return self.run(SimulationRequest(scenario_id=scenario.scenario_id), scenario)
        return self._recent_results[-1]

    @classmethod
    def _remember_result(cls, result: SimulationResult) -> None:
        cls._recent_results = [item for item in cls._recent_results if item.scenario_id != result.scenario_id]
        cls._recent_results.append(result)

    @staticmethod
    def _build_risk(engine_result) -> RiskClassification:
        level = engine_result.risk
        summary = engine_result.summary
        category = "thermal" if abs(summary.rear_carcass_temp_delta_c) >= abs(summary.spin_t05_delta_pct) else "stability"
        probability_map = {"low": 0.2, "medium-low": 0.35, "medium": 0.55, "high": 0.8}
        impact = min(
            1.0,
            max(
                abs(summary.rear_carcass_temp_delta_c) / 10.0,
                abs(summary.spin_t05_delta_pct) / 12.0,
                abs(summary.lap_time_delta_s) / 0.25,
            ),
        )

        return RiskClassification(
            risk_id=f"risk-{engine_result.scenario_id}",
            level=level,
            category=category,
            description=(
                f"{level.title()} risk based on spin delta {summary.spin_t05_delta_pct:.1f}%, "
                f"rear carcass delta {summary.rear_carcass_temp_delta_c:.1f} C and "
                f"lap delta {summary.lap_time_delta_s:.2f} s."
            ),
            probability=probability_map[level],
            impact=impact,
            mitigation_strategies=[
                "Replay with tighter setup bounds if risk is medium or higher.",
                "Review tire temperature and traction indicators before rollout.",
            ],
            evidence=list(engine_result.evidence),
        )
