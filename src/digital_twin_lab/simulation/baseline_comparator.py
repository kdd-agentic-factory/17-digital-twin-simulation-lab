from __future__ import annotations


class BaselineComparator:
    """Normalizes baseline/proposed metric comparison."""

    def compare(
        self,
        *,
        baseline_metrics: dict[str, float],
        proposed_metrics: dict[str, float],
        delta_metrics: dict[str, float],
    ) -> dict[str, dict[str, float]]:
        return {
            "baseline_metrics": baseline_metrics,
            "proposed_metrics": proposed_metrics,
            "delta_metrics": delta_metrics,
        }
