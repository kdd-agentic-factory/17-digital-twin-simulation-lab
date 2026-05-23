from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EngineSimulationSummary:
    spin_t05_delta_pct: float
    rear_carcass_temp_delta_c: float
    lap_time_delta_s: float
    degradation_delay_laps: int


@dataclass(slots=True)
class EngineSimulationResult:
    scenario_id: str
    risk: str
    summary: EngineSimulationSummary
    recommendation: str
    evidence: list[str] = field(default_factory=list)
    artifacts: dict[str, object] = field(default_factory=dict)


class ResultBuilder:
    """Builds coherent engine results from lower-level simulation artifacts."""

    def build(
        self,
        *,
        scenario_id: str,
        risk: str,
        lap_time_delta_s: float,
        stability_score_delta: float,
        rear_temp_delta_c: float,
        degradation_delay_laps: int,
        evidence: list[str],
        artifacts: dict[str, object],
    ) -> EngineSimulationResult:
        spin_delta = round(max(0.0, -stability_score_delta) * 42.0 + max(0.0, rear_temp_delta_c) * 0.08, 3)
        recommendation = "approve controlled rollout" if risk == "low" else "hold for engineering review"
        return EngineSimulationResult(
            scenario_id=scenario_id,
            risk=risk,
            summary=EngineSimulationSummary(
                spin_t05_delta_pct=spin_delta,
                rear_carcass_temp_delta_c=round(rear_temp_delta_c, 3),
                lap_time_delta_s=round(lap_time_delta_s, 3),
                degradation_delay_laps=degradation_delay_laps,
            ),
            recommendation=recommendation,
            evidence=evidence,
            artifacts=artifacts,
        )
