from __future__ import annotations

from digital_twin_lab.risk.risk_classifier import RiskAssessment, RiskClassifier


class PartRiskModel:
    def __init__(self, classifier: RiskClassifier | None = None) -> None:
        self._classifier = classifier or RiskClassifier()

    def assess(self, *, impact: dict[str, float], installation_confidence: float) -> RiskAssessment:
        delta_metrics = {
            "lap_time_delta_s": max(0.0, -impact.get("top_speed_delta_kph", 0.0) * -0.01),
            "stability_score_delta": impact.get("stability_delta", 0.0),
            "rear_temp_delta_c": abs(min(0.0, impact.get("rear_temp_delta_c", 0.0))) * (1.4 if installation_confidence > 0.85 else 0.8),
        }
        return self._classifier.classify(delta_metrics=delta_metrics, context={"component": "part"})
