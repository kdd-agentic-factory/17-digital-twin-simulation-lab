from __future__ import annotations


class MonteCarloRunner:
    """Produces deterministic uncertainty envelopes for the MVP."""

    def run(self, *, lap_time_delta_s: float, iterations: int) -> dict[str, float | int]:
        spread = round(max(0.01, abs(lap_time_delta_s) * 0.12), 3)
        return {
            "iterations": iterations,
            "lap_time_min_s": round(lap_time_delta_s - spread, 3),
            "lap_time_max_s": round(lap_time_delta_s + spread, 3),
            "lap_time_stddev_s": round(spread / 2, 3),
        }
