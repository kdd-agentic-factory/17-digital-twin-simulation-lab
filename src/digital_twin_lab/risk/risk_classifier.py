from __future__ import annotations

from dataclasses import dataclass

from digital_twin_lab.risk.approval_requirement_detector import ApprovalRequirementDetector


@dataclass(slots=True)
class RiskAssessment:
    level: str
    score: float
    approval_required: bool


class RiskClassifier:
    def __init__(self, detector: ApprovalRequirementDetector | None = None) -> None:
        self._detector = detector or ApprovalRequirementDetector()

    def classify(self, *, delta_metrics: dict[str, float], context: dict[str, str] | None = None) -> RiskAssessment:
        context = context or {}
        lap_penalty = max(0.0, delta_metrics.get("lap_time_delta_s", 0.0))
        stability_drop = max(0.0, -delta_metrics.get("stability_score_delta", 0.0))
        thermal_rise = max(0.0, delta_metrics.get("rear_temp_delta_c", 0.0))
        score = round(lap_penalty * 1.35 + stability_drop * 2.5 + thermal_rise * 0.055, 3)

        if score >= 0.95:
            level = "critical"
        elif score >= 0.55:
            level = "high"
        elif score >= 0.25:
            level = "medium"
        else:
            level = "low"

        return RiskAssessment(
            level=level,
            score=score,
            approval_required=self._detector.requires_approval(
                level,
                component=context.get("component", "setup"),
                score=score,
            ),
        )
