"""Simulation report builders."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from digital_twin_lab.models.report import SimulationReport
from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.models.simulation import SimulationResult


class ReportService:
    """Creates structured report payloads from simulation outputs."""

    _latest_report: SimulationReport | None = None

    def generate_report(
        self,
        simulation_result: SimulationResult,
        scenario: SimulationScenario | None = None,
    ) -> SimulationReport:
        """Generate a lightweight report model for API responses or persistence."""
        findings = [
            f"Risk level classified as {simulation_result.risk_classification.level}.",
            f"Lap-time delta projected at {simulation_result.summary.lap_time_delta_s:.2f} s.",
            f"Degradation delay estimated at {simulation_result.summary.degradation_delay_laps} laps.",
        ]

        summary = {
            "scenario_id": simulation_result.scenario_id,
            "generated_at": datetime.now().isoformat(),
            "scenario_type": scenario.scenario_type if scenario else simulation_result.metadata.get("scenario_type"),
            "lap_time_delta_s": simulation_result.summary.lap_time_delta_s,
            "risk_level": simulation_result.risk_classification.level,
        }

        risks = [
            {
                "level": simulation_result.risk_classification.level,
                "category": simulation_result.risk_classification.category,
                "probability": simulation_result.risk_classification.probability,
                "impact": simulation_result.risk_classification.impact,
                "description": simulation_result.risk_classification.description,
            }
        ]

        recommendations = [
            {
                "title": "Primary recommendation",
                "action": simulation_result.recommendation,
                "evidence_count": len(simulation_result.evidence),
            }
        ]

        metadata = dict(simulation_result.metadata)
        if scenario is not None:
            metadata["scenario_name"] = scenario.name
            metadata["circuit_id"] = scenario.circuit_id

        report = SimulationReport(
            report_id=f"report-{uuid4()}",
            scenario_id=simulation_result.scenario_id,
            summary=summary,
            key_findings=findings,
            risks=risks,
            recommendations=recommendations,
            visualizations=[],
            metadata=metadata,
        )
        self.__class__._latest_report = report
        return report

    def generate_latest_report(
        self,
        simulation_result: SimulationResult,
        scenario: SimulationScenario | None = None,
    ) -> SimulationReport:
        return self.generate_report(simulation_result, scenario)

    def get_latest_report(self) -> SimulationReport:
        if self.__class__._latest_report is None:
            from digital_twin_lab.services.scenario_service import ScenarioService
            from digital_twin_lab.services.simulation_service import SimulationService

            simulation_service = SimulationService()
            latest_simulation = simulation_service.latest_result()
            scenario_service = ScenarioService()
            scenario = None
            try:
                scenario = scenario_service.get_scenario(latest_simulation.scenario_id)
            except Exception:
                scenario = None
            return self.generate_report(latest_simulation, scenario)
        return self.__class__._latest_report
