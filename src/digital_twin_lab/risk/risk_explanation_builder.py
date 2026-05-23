from __future__ import annotations


class RiskExplanationBuilder:
    def build(self, *, risk_level: str, delta_metrics: dict[str, float], component: str) -> str:
        return (
            f"{component.title()} risk is {risk_level} because lap delta is "
            f"{delta_metrics.get('lap_time_delta_s', 0.0):.3f}s, stability delta is "
            f"{delta_metrics.get('stability_score_delta', 0.0):.3f} and rear temperature delta is "
            f"{delta_metrics.get('rear_temp_delta_c', 0.0):.2f}C."
        )
