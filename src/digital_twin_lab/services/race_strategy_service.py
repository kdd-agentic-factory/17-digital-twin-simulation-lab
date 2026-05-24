"""Race strategy optimisation using the Pacejka tire model.

Evaluates all 1-stop and 2-stop strategies over a configurable pit-lap window
and returns the minimum total race time with per-lap telemetry.
"""

from __future__ import annotations

import itertools
import uuid
from pathlib import Path

import yaml

from digital_twin_lab.models.race_strategy import (
    LapData,
    RaceStrategyRequest,
    RaceStrategyResult,
    StintSpec,
    StintSummary,
    StrategyVariant,
)
from digital_twin_lab.tire.pacejka_model import PacejkaTireModel

_PROFILES_DIR = Path(__file__).parent.parent / "data" / "circuit_profiles"


def _load_circuit(circuit_id: str) -> dict:
    path = _PROFILES_DIR / f"{circuit_id}.yaml"
    if not path.exists():
        # Default fallback so the service never crashes on unknown circuits
        return {"base_lap_time_s": 100.0, "thermal_load": 0.65, "stability_bias": 0.74, "avg_speed_ms": 50.0}
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


class RaceStrategyService:
    """Optimises a MotoGP race tyre strategy using Pacejka-based degradation."""

    def simulate(self, request: RaceStrategyRequest) -> RaceStrategyResult:
        circuit = _load_circuit(request.circuit_id)
        base_lap_s = float(circuit.get("base_lap_time_s", 100.0))
        compounds = list(request.compounds)
        n_stops = len(compounds) - 1

        # Build candidate pit-lap windows
        # For each inter-stint boundary we test laps from 25% to 70% of total
        window_start = max(3, int(request.race_laps * 0.25))
        window_end = min(request.race_laps - 3, int(request.race_laps * 0.70))

        if n_stops == 0:
            candidates = [()]
        elif n_stops == 1:
            candidates = [(p,) for p in range(window_start, window_end + 1)]
        else:
            half = (window_end - window_start) // 2
            candidates = [
                (p1, p2)
                for p1 in range(window_start, window_start + half + 1)
                for p2 in range(window_start + half + 2, window_end + 1)
                if p1 < p2
            ]

        variants: list[tuple[tuple[int, ...], float]] = []
        for pit_laps in candidates:
            total = self._total_time(
                pit_laps, compounds, request.race_laps, base_lap_s,
                circuit, request.ambient_temp_c, request.track_temp_c,
                request.pit_stop_penalty_s, request.setup_stability_score,
            )
            variants.append((pit_laps, total))

        variants.sort(key=lambda v: v[1])
        best_pit_laps, best_time = variants[0]

        # Build ranked alternatives list (top-10 max)
        alternatives = [
            StrategyVariant(pit_laps=list(p), total_race_time_s=round(t, 3), rank=i + 1)
            for i, (p, t) in enumerate(variants[:10])
        ]

        # Build full lap-by-lap breakdown for optimal strategy
        lap_by_lap, stint_summaries = self._full_breakdown(
            best_pit_laps, compounds, request.race_laps, base_lap_s,
            circuit, request.ambient_temp_c, request.track_temp_c,
            request.setup_stability_score,
        )

        recommendation = self._make_recommendation(best_pit_laps, compounds, best_time, request.race_laps)

        return RaceStrategyResult(
            strategy_id=str(uuid.uuid4()),
            circuit_id=request.circuit_id,
            race_laps=request.race_laps,
            total_race_time_s=round(best_time, 3),
            pit_stops=n_stops,
            pit_stop_penalty_s=request.pit_stop_penalty_s,
            compounds_used=compounds,
            optimal_pit_laps=list(best_pit_laps),
            stints=stint_summaries,
            lap_by_lap=lap_by_lap,
            alternatives_evaluated=alternatives,
            recommendation=recommendation,
            limitations=[
                "Physics uses Pacejka MF-94 with Archard wear law — real compounds may differ.",
                "Weather changes, safety car periods, and tyre pressure transients not modelled.",
                "Pit stop penalty is fixed; real delta varies with pit lane length and crew time.",
            ],
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stint_boundaries(self, pit_laps: tuple[int, ...], race_laps: int) -> list[tuple[int, int]]:
        """Return (start_lap, end_lap) inclusive for each stint."""
        boundaries = []
        prev = 1
        for pl in pit_laps:
            boundaries.append((prev, pl))
            prev = pl + 1
        boundaries.append((prev, race_laps))
        return boundaries

    def _total_time(
        self,
        pit_laps: tuple[int, ...],
        compounds: list[str],
        race_laps: int,
        base_lap_s: float,
        circuit: dict,
        ambient_temp_c: float,
        track_temp_c: float,
        pit_penalty_s: float,
        stability_score: float,
    ) -> float:
        boundaries = self._stint_boundaries(pit_laps, race_laps)
        total = 0.0
        for stint_idx, (start, end) in enumerate(boundaries):
            compound = compounds[min(stint_idx, len(compounds) - 1)]
            model = PacejkaTireModel(compound)  # type: ignore[arg-type]
            stint_laps = end - start + 1
            result = model.simulate_stint(
                laps=stint_laps,
                circuit_profile=circuit,
                ambient_temp_c=ambient_temp_c,
                track_temp_c=track_temp_c,
                setup_stability_score=stability_score,
            )
            for state in result.laps:
                total += base_lap_s + state.lap_time_delta_s
        total += pit_penalty_s * len(pit_laps)
        return total

    def _full_breakdown(
        self,
        pit_laps: tuple[int, ...],
        compounds: list[str],
        race_laps: int,
        base_lap_s: float,
        circuit: dict,
        ambient_temp_c: float,
        track_temp_c: float,
        stability_score: float,
    ) -> tuple[list[LapData], list[StintSummary]]:
        boundaries = self._stint_boundaries(pit_laps, race_laps)
        lap_data: list[LapData] = []
        stint_summaries: list[StintSummary] = []
        cumulative = 0.0
        global_lap = 1

        for stint_idx, (start, end) in enumerate(boundaries):
            compound = compounds[min(stint_idx, len(compounds) - 1)]
            model = PacejkaTireModel(compound)  # type: ignore[arg-type]
            stint_laps = end - start + 1
            result = model.simulate_stint(
                laps=stint_laps,
                circuit_profile=circuit,
                ambient_temp_c=ambient_temp_c,
                track_temp_c=track_temp_c,
                setup_stability_score=stability_score,
            )
            stint_lap_times: list[float] = []
            for state in result.laps:
                lt = base_lap_s + state.lap_time_delta_s
                cumulative += lt
                stint_lap_times.append(lt)
                lap_data.append(LapData(
                    lap=global_lap,
                    stint=stint_idx + 1,
                    compound=compound,  # type: ignore[arg-type]
                    wear_pct=state.wear_pct,
                    carcass_temp_c=state.carcass_temp_c,
                    grip_factor=state.grip_factor,
                    lap_time_s=round(lt, 3),
                    cumulative_time_s=round(cumulative, 3),
                ))
                global_lap += 1

            final_state = result.laps[-1] if result.laps else None
            avg_lt = sum(stint_lap_times) / len(stint_lap_times) if stint_lap_times else base_lap_s
            stint_summaries.append(StintSummary(
                stint=stint_idx + 1,
                compound=compound,  # type: ignore[arg-type]
                start_lap=start,
                end_lap=end,
                stint_laps=stint_laps,
                cliff_lap=result.cliff_lap,
                final_wear_pct=final_state.wear_pct if final_state else 0.0,
                avg_lap_time_s=round(avg_lt, 3),
            ))

        return lap_data, stint_summaries

    @staticmethod
    def _make_recommendation(pit_laps: tuple[int, ...], compounds: list[str], total_time_s: float, race_laps: int) -> str:
        if not pit_laps:
            return f"No-stop strategy on {compounds[0]} compound. Total race time {total_time_s:.1f} s."
        pit_str = " + ".join(f"L{p}" for p in pit_laps)
        compound_str = " → ".join(compounds)
        return (
            f"Optimal {len(pit_laps)}-stop strategy: pit at {pit_str} ({compound_str}). "
            f"Projected total race time {total_time_s:.1f} s over {race_laps} laps."
        )
