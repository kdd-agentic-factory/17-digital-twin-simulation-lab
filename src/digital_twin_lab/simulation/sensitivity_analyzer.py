from __future__ import annotations


class SensitivityAnalyzer:
    """Ranks changed setup parameters by absolute delta magnitude."""

    def analyze(self, changed_parameters: dict[str, dict[str, object]]) -> list[str]:
        ranked = sorted(
            changed_parameters.items(),
            key=lambda item: abs(item[1].get("delta", 0)) if isinstance(item[1].get("delta", 0), (int, float)) else 1,
            reverse=True,
        )
        return [name for name, _ in ranked]
