from __future__ import annotations


class UncertaintyEstimator:
    """Converts Monte Carlo spread into a confidence band."""

    def estimate(self, monte_carlo_summary: dict[str, float | int]) -> dict[str, float]:
        stddev = float(monte_carlo_summary.get("lap_time_stddev_s", 0.02))
        confidence = max(0.5, round(1.0 - stddev, 3))
        return {"lap_time_stddev_s": stddev, "confidence": confidence}
