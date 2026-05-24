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
        from digital_twin_lab.tire.pacejka_model import PacejkaTireModel

        circuit_profile = self._catalog.load("circuit_profiles", f"{circuit_id}.yaml")

        # Use Pacejka physics-based prediction when compound is known
        pacejka_compound = compound if compound in ("soft", "medium", "hard") else "medium"
        pacejka = PacejkaTireModel(pacejka_compound)  # type: ignore[arg-type]
        stability_score = max(0.3, 1.0 - aggression_index)
        pacejka_result = pacejka.predict_collapse(
            current_wear_pct=current_wear_pct,
            current_temp_c=current_carcass_temp_c,
            remaining_laps=stint_laps,
            circuit_profile=circuit_profile,
            ambient_temp_c=float(circuit_profile.get("ambient_temp_c", 30.0)),
            setup_stability_score=stability_score,
        )

        # Legacy collapse_predictor for API response shape compatibility
        degradation_index = pacejka_result["degradation_index"]
        collapse_prediction = self._collapse_predictor.predict(
            degradation_index=degradation_index, stint_laps=stint_laps
        )
        return {
            "tire_id": tire_id,
            "degradation_index": degradation_index,
            "risk_level": pacejka_result["risk_level"],
            "collapse_prediction": collapse_prediction,
            "pacejka": {
                "collapse_predicted": pacejka_result["collapse_predicted"],
                "collapse_lap": pacejka_result["collapse_lap"],
                "remaining_laps_safe": pacejka_result["remaining_laps_safe"],
                "final_wear_pct": pacejka_result["final_wear_pct"],
                "final_temp_c": pacejka_result["final_temp_c"],
            },
        }
