"""Recommendation validation orchestration."""

from __future__ import annotations

from digital_twin_lab.parts import PartValidationService
from digital_twin_lab.setup import SetupRecommendationValidator


class RecommendationValidationService:
    def __init__(self) -> None:
        self._validator = SetupRecommendationValidator()
        self._parts = PartValidationService()

    def validate(self, *, recommendation_id: str, scenario_id: str, recommendation_risk: str, part_id: str, circuit_id: str, confidence: float, ambient_temp_c: float, track_temp_c: float) -> dict[str, object]:
        simulation = self._parts.simulate(
            part_id=part_id,
            circuit_id=circuit_id,
            installation_confidence=confidence,
            ambient_temp_c=ambient_temp_c,
            track_temp_c=track_temp_c,
        )
        allowed, reasons = self._validator.validate(
            claimed_risk_level=recommendation_risk,
            simulated_risk_level=str(simulation["risk_level"]),
            approval_required=bool(simulation["approval_required"]),
        )
        return {
            "recommendation_id": recommendation_id,
            "scenario_id": scenario_id,
            "allowed": allowed,
            "blocked": not allowed,
            "risk_level": simulation["risk_level"],
            "approval_required": simulation["approval_required"],
            "reasons": reasons or [str(simulation["explanation"])],
            "simulation": simulation,
        }
