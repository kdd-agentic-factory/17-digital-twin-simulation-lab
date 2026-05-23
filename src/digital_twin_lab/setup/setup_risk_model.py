from __future__ import annotations

from digital_twin_lab.risk.risk_classifier import RiskAssessment, RiskClassifier


class SetupRiskModel:
    def __init__(self, classifier: RiskClassifier | None = None) -> None:
        self._classifier = classifier or RiskClassifier()

    def assess(self, delta_metrics: dict[str, float]) -> RiskAssessment:
        return self._classifier.classify(delta_metrics=delta_metrics, context={"component": "setup"})
