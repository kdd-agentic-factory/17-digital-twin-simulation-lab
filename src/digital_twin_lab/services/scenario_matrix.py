"""Digital Twin Report — multi-scenario batch simulation (crew-chief notes).

"Quiero visualizar más escenarios con más datos y más capacidad de predecir."

Sweeps the strategy space — compound × initial pressure × rider aggression — and
predicts each scenario's stint outcome (does it survive, collapse lap, mean
degradation, end-of-stint grip, estimated lap-time loss), then ranks them so the
engineer can compare many what-ifs at a glance. Reuses the pressure-variant wear
model (``pressure_sweep``) so it stays consistent with the tyre physics.
"""

from __future__ import annotations

from itertools import product
from typing import Any

from digital_twin_lab.services import pressure_sweep as ps

# Lap-time penalty per % of tyre wear (s/lap), and aggression's wear multiplier.
_LAPTIME_S_PER_WEAR = 0.012
_AGGR_WEAR_MULT = {"low": 0.85, "medium": 1.0, "high": 1.2}


def _scenario(compound: str, pressure: float, aggression: str, stint_laps: int) -> dict[str, Any]:
    v = ps.predict_variant(compound, pressure, stint_laps)
    mult = _AGGR_WEAR_MULT.get(aggression, 1.0)
    wear_per_lap = round(v["wear_per_lap_pct"] * mult, 4)
    final_wear = round(min(wear_per_lap * stint_laps, 100.0), 1)
    laps_to_cliff = round((ps.CLIFF_WEAR_PCT / wear_per_lap) if wear_per_lap > 0 else 999.0, 1)
    survives = final_wear < ps.CLIFF_WEAR_PCT
    # mean lap-time loss vs fresh over the stint (≈ wear at mid-stint)
    laptime_loss = round(_LAPTIME_S_PER_WEAR * (final_wear / 2.0), 3)
    return {
        "compound": compound,
        "pressure_bar": round(pressure, 2),
        "aggression": aggression,
        "wear_per_lap_pct": wear_per_lap,
        "final_wear_pct": final_wear,
        "laps_to_cliff": laps_to_cliff,
        "end_grip_index": v["grip_index"],
        "avg_laptime_loss_s": laptime_loss,
        "survives_stint": survives,
    }


def run_scenario_matrix(
    compounds: list[str],
    pressures_bar: list[float],
    aggressions: list[str],
    stint_laps: int,
) -> dict[str, Any]:
    """Run the full compound × pressure × aggression scenario sweep."""
    scenarios = [
        _scenario(c, p, a, stint_laps)
        for c, p, a in product(compounds, pressures_bar, aggressions)
    ]
    survivors = [s for s in scenarios if s["survives_stint"]]
    # Best = survives with the best end-grip, lowest lap-time loss; else longest life.
    best = (
        min(survivors, key=lambda s: (-s["end_grip_index"], s["avg_laptime_loss_s"]))
        if survivors else max(scenarios, key=lambda s: s["laps_to_cliff"])
    )
    return {
        "stint_laps": stint_laps,
        "scenario_count": len(scenarios),
        "survivor_count": len(survivors),
        "scenarios": scenarios,
        "recommended": best,
        "conclusion": (
            f"{len(survivors)}/{len(scenarios)} scenarios last the {stint_laps}-lap stint. "
            f"Best: {best['compound']} @ {best['pressure_bar']} bar, {best['aggression']} pace "
            f"({best['avg_laptime_loss_s']}s/lap avg loss, end-grip {best['end_grip_index']})."
        ),
    }
