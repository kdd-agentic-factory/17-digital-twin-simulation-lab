from __future__ import annotations


class UnsafeRecommendationBlocker:
    def should_block(self, *, risk_level: str, approval_required: bool, claimed_risk_level: str | None = None) -> bool:
        if risk_level in {"high", "critical"}:
            return True
        if claimed_risk_level and claimed_risk_level != risk_level and approval_required:
            return True
        return False
