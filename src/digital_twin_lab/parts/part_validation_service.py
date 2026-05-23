from __future__ import annotations

from digital_twin_lab.parts.part_impact_model import PartImpactModel
from digital_twin_lab.parts.part_risk_model import PartRiskModel
from digital_twin_lab.risk.risk_explanation_builder import RiskExplanationBuilder
from digital_twin_lab.utils.catalog import Catalog


class PartValidationService:
    def __init__(self, catalog: Catalog | None = None) -> None:
        self._catalog = catalog or Catalog()
        self._impact_model = PartImpactModel()
        self._risk_model = PartRiskModel()
        self._explanation_builder = RiskExplanationBuilder()

    def simulate(
        self,
        *,
        part_id: str,
        circuit_id: str,
        installation_confidence: float,
        ambient_temp_c: float,
        track_temp_c: float,
    ) -> dict[str, object]:
        part_model = self._catalog.load("part_models", f"{part_id}.yaml")
        circuit_profile = self._catalog.load("circuit_profiles", f"{circuit_id}.yaml")
        impact = self._impact_model.evaluate(
            part_model=part_model,
            circuit_profile=circuit_profile,
            ambient_temp_c=ambient_temp_c,
            track_temp_c=track_temp_c,
        )
        risk = self._risk_model.assess(impact=impact, installation_confidence=installation_confidence)
        return {
            "part_id": part_id,
            "impact": impact,
            "risk_level": risk.level,
            "approval_required": risk.approval_required,
            "explanation": self._explanation_builder.build(
                risk_level=risk.level,
                delta_metrics={
                    "lap_time_delta_s": round(-impact.get("top_speed_delta_kph", 0.0) * 0.01, 3),
                    "stability_score_delta": impact.get("stability_delta", 0.0),
                    "rear_temp_delta_c": impact.get("rear_temp_delta_c", 0.0),
                },
                component="part",
            ),
        }
