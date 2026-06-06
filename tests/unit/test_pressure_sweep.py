"""Tests for tyre pressure-variant degradation prediction (crew-chief notes / §7)."""

from __future__ import annotations

import pytest

from digital_twin_lab.services import pressure_sweep as ps


def test_wear_factor_minimum_at_optimum():
    opt = ps._OPTIMAL_BAR["medium"]
    assert ps.pressure_wear_factor(opt, opt) == 1.0
    assert ps.pressure_wear_factor(opt - 0.2, opt) > 1.0
    assert ps.pressure_wear_factor(opt + 0.2, opt) > 1.0
    # under-pressure penalised more than the same over-pressure
    assert ps.pressure_wear_factor(opt - 0.2, opt) > ps.pressure_wear_factor(opt + 0.2, opt)


def test_predict_variant_at_optimum_uses_base_wear():
    v = ps.predict_variant("soft", ps._OPTIMAL_BAR["soft"], stint_laps=20)
    assert v["wear_per_lap_pct"] == pytest.approx(ps._BASE_WEAR["soft"])
    assert v["grip_index"] == pytest.approx(1.0)
    assert v["pressure_bar"] == ps._OPTIMAL_BAR["soft"]


def test_deviation_increases_wear_and_drops_grip():
    opt = ps._OPTIMAL_BAR["medium"]
    base = ps.predict_variant("medium", opt, 20)
    low = ps.predict_variant("medium", opt - 0.25, 20)
    assert low["wear_per_lap_pct"] > base["wear_per_lap_pct"]
    assert low["grip_index"] < base["grip_index"]
    assert low["est_carcass_temp_c"] > base["est_carcass_temp_c"]  # under-pressure hotter


def test_sweep_recommends_near_optimum():
    res = ps.sweep("medium", [1.6, 1.8, 1.95, 2.1, 2.3], stint_laps=18)
    assert len(res["variants"]) == 5
    # recommended pressure should be the optimum (best grip among survivors)
    assert res["recommended_pressure_bar"] == pytest.approx(1.95, abs=0.01)
    assert "bar" in res["recommendation"]


def test_unknown_compound_falls_back_to_medium():
    res = ps.sweep("supersoft", [1.9, 2.0], stint_laps=10)
    assert res["compound"] == "medium"
