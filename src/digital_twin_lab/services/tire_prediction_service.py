"""Tire prediction and degradation orchestration."""

from __future__ import annotations

from digital_twin_lab.models.tire import TireState
from digital_twin_lab.risk.risk_classifier import RiskClassifier
from digital_twin_lab.tire.collapse_predictor import CollapsePredictor
from digital_twin_lab.tire.degradation import TireDegradationModel
from digital_twin_lab.utils.catalog import Catalog


class TirePredictionService:
    """Provides API-ready tire degradation and collapse-risk projections."""

    def __init__(self, degradation_model: TireDegradationModel | None = None) -> None:
        self.degradation_model = degradation_model or TireDegradationModel()
        self._catalog = Catalog()
        self._classifier = RiskClassifier()
        self._collapse_predictor = CollapsePredictor()

    def predict_stint(
        self,
        tire_state: TireState,
        *,
        laps_to_simulate: int,
        temp_delta_c: float = 0.0,
        spin_delta_pct: float = 0.0,
        tcs_active: bool = False,
    ) -> dict[str, float | int | bool | str]:
        """Project tire wear and failure exposure over a short stint."""
        projected_wear = tire_state.wear_pct
        for lap in range(1, laps_to_simulate + 1):
            projected_wear = self.degradation_model.calculate_degradation(
                current_wear=projected_wear,
                temp_delta_c=temp_delta_c,
                spin_delta_pct=spin_delta_pct,
                tcs_active=tcs_active,
                lap_number=lap,
            )

        projected_temp = tire_state.carcass_temp_c + temp_delta_c
        collapse_risk = self.assess_collapse_risk(
            projected_wear_pct=projected_wear,
            projected_carcass_temp_c=projected_temp,
        )

        return {
            "tire_id": tire_state.tire_id,
            "projected_wear_pct": round(projected_wear, 3),
            "projected_carcass_temp_c": round(projected_temp, 3),
            "degradation_delay_laps": self.degradation_model.estimate_degradation_delay(temp_delta_c, spin_delta_pct),
            "collapse_risk": collapse_risk,
        }

    def assess_collapse_risk(
        self,
        *,
        projected_wear_pct: float,
        projected_carcass_temp_c: float,
    ) -> str:
        """Classify simplified tire collapse risk for API responses."""
        if projected_wear_pct >= 92.0 or projected_carcass_temp_c >= 135.0:
            return "critical"
        if projected_wear_pct >= 80.0 or projected_carcass_temp_c >= 120.0:
            return "high"
        if projected_wear_pct >= 65.0 or projected_carcass_temp_c >= 108.0:
            return "medium"
        return "low"

    def predict_collapse(
        self,
        *,
        tire_id: str,
        compound: str,
        circuit_id: str,
        current_wear_pct: float,
        current_carcass_temp_c: float,
        stint_laps: int,
        aggression_index: float,
    ) -> dict[str, object]:
        tire_model = self._catalog.load("tire_models", f"{compound}.yaml")
        circuit_profile = self._catalog.load("circuit_profiles", f"{circuit_id}.yaml")
        degradation_index = round(
            current_wear_pct / 100 * 0.46
            + current_carcass_temp_c / 140 * 0.22
            + aggression_index * 0.18
            + float(tire_model["thermal_sensitivity"]) * 0.08
            + float(circuit_profile["thermal_load"]) * 0.16,
            3,
        )
        collapse_prediction = self._collapse_predictor.predict(degradation_index=degradation_index, stint_laps=stint_laps)
        risk = self._classifier.classify(
            delta_metrics={
                "lap_time_delta_s": max(0.0, degradation_index - 0.68),
                "stability_score_delta": -max(0.0, degradation_index - 0.72) * 0.2,
                "rear_temp_delta_c": max(0.0, current_carcass_temp_c - float(tire_model["optimal_carcass_temp_c"])),
            },
            context={"component": "tire"},
        )
        return {
            "tire_id": tire_id,
            "degradation_index": degradation_index,
            "risk_level": risk.level,
            "collapse_prediction": collapse_prediction,
        }
