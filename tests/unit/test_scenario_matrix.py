"""Tests for the Digital Twin Report multi-scenario matrix."""

from __future__ import annotations

from digital_twin_lab.services import scenario_matrix as sm


def test_matrix_size_and_ranking():
    res = sm.run_scenario_matrix(
        compounds=["soft", "medium", "hard"],
        pressures_bar=[1.8, 1.95, 2.1],
        aggressions=["low", "medium", "high"],
        stint_laps=18,
    )
    assert res["scenario_count"] == 3 * 3 * 3
    assert 0 <= res["survivor_count"] <= res["scenario_count"]
    # recommended must be one of the scenarios
    assert res["recommended"] in res["scenarios"]
    assert "Best:" in res["conclusion"]


def test_aggression_increases_wear():
    low = sm._scenario("medium", 1.95, "low", 20)
    high = sm._scenario("medium", 1.95, "high", 20)
    assert high["wear_per_lap_pct"] > low["wear_per_lap_pct"]
    assert high["final_wear_pct"] >= low["final_wear_pct"]


def test_short_stint_all_survive():
    res = sm.run_scenario_matrix(["medium"], [1.95], ["low"], stint_laps=3)
    assert res["survivor_count"] == 1
    assert res["recommended"]["survives_stint"] is True
