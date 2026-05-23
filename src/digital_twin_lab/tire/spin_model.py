from __future__ import annotations


class SpinModel:
    """Estimates spin exposure from stability and thermal deltas."""

    def estimate_spin_delta_pct(self, *, stability_score_delta: float, rear_temp_delta_c: float) -> float:
        return round(max(0.0, -stability_score_delta) * 42.0 + max(0.0, rear_temp_delta_c) * 0.08, 3)
