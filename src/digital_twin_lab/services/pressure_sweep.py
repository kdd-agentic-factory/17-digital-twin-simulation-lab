"""Tyre pressure-variant degradation prediction (crew-chief notes / Spec §7).

This class has *no pit stops* and *no strategy optimiser*: the compound must last
to the flag, so the engineer works the **initial pressure** instead. This module
predicts tyre degradation / laps-to-cliff across a sweep of cold pressures — the
pressure analogue of the Setup Impact Estimator — and flags the optimal window.

Pressure model (physics-informed heuristic):
  * Every compound has an optimal cold pressure; deviation raises the wear rate
    via an **asymmetric parabola** — under-pressure flexes the carcass and over-
    heats it (steeper penalty), over-pressure shrinks the contact patch and
    slides (milder penalty).
  * Reference wear rates come from the Pacejka model's per-compound ``k_wear``
    (%/lap at reference load), so this stays consistent with the collapse model.
"""

from __future__ import annotations

from typing import Any

# Optimal cold pressure (bar) per compound — front reference values.
_OPTIMAL_BAR = {"soft": 1.90, "medium": 1.95, "hard": 2.00}
# Reference wear %/lap per compound (mirrors PacejkaTireModel k_wear).
_BASE_WEAR = {"soft": 2.5, "medium": 1.5, "hard": 0.85}
CLIFF_WEAR_PCT = 70.0
_K_UNDER, _K_OVER = 3.2, 1.8  # parabola steepness under / over optimal


def pressure_wear_factor(pressure_bar: float, optimal_bar: float) -> float:
    """Wear-rate multiplier vs the optimal pressure (1.0 at optimum, ≥1 away)."""
    d = pressure_bar - optimal_bar
    k = _K_UNDER if d < 0 else _K_OVER
    return round(1.0 + k * d * d, 4)


def predict_variant(
    compound: str,
    pressure_bar: float,
    stint_laps: int,
    start_wear_pct: float = 0.0,
) -> dict[str, Any]:
    """Predict degradation for one cold-pressure variant."""
    comp = compound if compound in _BASE_WEAR else "medium"
    optimal = _OPTIMAL_BAR[comp]
    base = _BASE_WEAR[comp]
    factor = pressure_wear_factor(pressure_bar, optimal)
    wear_per_lap = round(base * factor, 4)

    d = pressure_bar - optimal
    # Under-pressure runs hotter (flex), over-pressure cooler but sliding.
    est_temp_c = round(95.0 - d * 45.0, 1)
    laps_to_cliff = (CLIFF_WEAR_PCT - start_wear_pct) / wear_per_lap if wear_per_lap > 0 else 999.0
    final_wear = round(start_wear_pct + wear_per_lap * stint_laps, 1)
    # Grip index: best at optimum, falls with the wear factor.
    grip_index = round(1.0 / factor, 3)
    return {
        "pressure_bar": round(pressure_bar, 2),
        "wear_per_lap_pct": wear_per_lap,
        "laps_to_cliff": round(laps_to_cliff, 1),
        "final_wear_pct": min(final_wear, 100.0),
        "est_carcass_temp_c": est_temp_c,
        "grip_index": grip_index,
        "survives_stint": final_wear < CLIFF_WEAR_PCT,
    }


def sweep(
    compound: str,
    pressures_bar: list[float],
    stint_laps: int,
    start_wear_pct: float = 0.0,
) -> dict[str, Any]:
    """Sweep a list of cold pressures → per-variant prediction + optimal window."""
    variants = [predict_variant(compound, p, stint_laps, start_wear_pct) for p in pressures_bar]
    # Optimal = survives the stint with the most grip; else the one that lasts longest.
    survivors = [v for v in variants if v["survives_stint"]]
    optimal = (max(survivors, key=lambda v: v["grip_index"]) if survivors
               else max(variants, key=lambda v: v["laps_to_cliff"]))
    comp = compound if compound in _BASE_WEAR else "medium"
    return {
        "compound": comp,
        "optimal_pressure_bar": _OPTIMAL_BAR[comp],
        "recommended_pressure_bar": optimal["pressure_bar"],
        "stint_laps": stint_laps,
        "variants": variants,
        "recommendation": (
            f"Run {optimal['pressure_bar']:.2f} bar ({comp}) — "
            f"{'survives the stint' if optimal['survives_stint'] else 'longest life'} at "
            f"{optimal['wear_per_lap_pct']:.2f} %/lap, grip {optimal['grip_index']:.2f}."
        ),
    }
