from __future__ import annotations


class ApprovalRequirementDetector:
    def requires_approval(self, risk_level: str, *, component: str = "setup", score: float = 0.0) -> bool:
        if risk_level in {"high", "critical"}:
            return True
        return risk_level == "medium" and (component == "part" or score >= 0.45)
