"""What-if orchestration over deterministic MVP models."""

from __future__ import annotations

from digital_twin_lab.risk.risk_explanation_builder import RiskExplanationBuilder
from digital_twin_lab.setup import SetupImpactModel, SetupRiskModel
from digital_twin_lab.utils.catalog import Catalog


class WhatIfService:
    def __init__(self, catalog: Catalog | None = None) -> None:
        self._catalog = catalog or Catalog()
        self._impact_model = SetupImpactModel()
        self._risk_model = SetupRiskModel()
        self._explanation_builder = RiskExplanationBuilder()

    def simulate(
        self,
        *,
        scenario_id: str,
        circuit_id: str,
        baseline_setup_id: str,
        proposed_setup: dict[str, object],
        ambient_temp_c: float,
        track_temp_c: float,
        laps: int,
    ) -> dict[str, object]:
        baseline_setup = self._catalog.load("baseline_setups", f"{baseline_setup_id}.yaml")
        circuit_profile = self._catalog.load("circuit_profiles", f"{circuit_id}.yaml")
        baseline_metrics, proposed_metrics, delta_metrics, diff = self._impact_model.evaluate(
            baseline_setup=baseline_setup,
            proposed_setup={**baseline_setup, **proposed_setup},
            circuit_profile=circuit_profile,
            ambient_temp_c=ambient_temp_c,
            track_temp_c=track_temp_c,
            laps=laps,
        )
        risk = self._risk_model.assess(delta_metrics)
        return {
            "scenario_id": scenario_id,
            "baseline_metrics": baseline_metrics,
            "proposed_metrics": proposed_metrics,
            "delta_metrics": delta_metrics,
            "risk_level": risk.level,
            "approval_required": risk.approval_required,
            "explanation": self._explanation_builder.build(risk_level=risk.level, delta_metrics=delta_metrics, component="setup"),
            "changed_parameters": diff.changed_parameters,
            "limitations": [
                "MVP uses deterministic heuristics instead of full-fidelity vehicle dynamics.",
                "Curb strikes, wind gusts and rider adaptation are not modelled.",
            ],
        }

    def load_circuit_profile(self, circuit_id: str) -> dict[str, object]:
        return self._catalog.load("circuit_profiles", f"{circuit_id}.yaml")
