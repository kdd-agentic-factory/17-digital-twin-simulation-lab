from __future__ import annotations

from digital_twin_lab.risk.unsafe_recommendation_blocker import UnsafeRecommendationBlocker


class SetupRecommendationValidator:
    def __init__(self, blocker: UnsafeRecommendationBlocker | None = None) -> None:
        self._blocker = blocker or UnsafeRecommendationBlocker()

    def validate(self, *, claimed_risk_level: str, simulated_risk_level: str, approval_required: bool) -> tuple[bool, list[str]]:
        blocked = self._blocker.should_block(
            risk_level=simulated_risk_level,
            approval_required=approval_required,
            claimed_risk_level=claimed_risk_level,
        )
        reasons: list[str] = []
        if claimed_risk_level != simulated_risk_level:
            reasons.append("Recommendation risk statement does not match simulation evidence.")
        if approval_required:
            reasons.append("Crew chief approval is required before rollout.")
        return (not blocked), reasons
