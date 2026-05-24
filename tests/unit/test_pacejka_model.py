"""Unit tests for the Pacejka Magic Formula tire model."""

from __future__ import annotations

import pytest

from digital_twin_lab.tire.pacejka_model import PacejkaTireModel, StintSimResult, TireLapState

_JEREZ = {"base_lap_time_s": 98.214, "thermal_load": 0.68, "stability_bias": 0.74, "avg_speed_ms": 52.0}


class TestPacejkaPhysics:
    def test_longitudinal_force_zero_at_zero_slip(self):
        model = PacejkaTireModel("medium")
        force = model.longitudinal_force_n(slip_ratio=0.0, normal_load_n=845.0, temp_factor=1.0)
        assert force == pytest.approx(0.0, abs=1e-6)

    def test_longitudinal_force_positive_for_positive_slip(self):
        model = PacejkaTireModel("medium")
        force = model.longitudinal_force_n(slip_ratio=0.1, normal_load_n=845.0, temp_factor=1.0)
        assert force > 0.0

    def test_longitudinal_force_saturates_at_high_slip(self):
        model = PacejkaTireModel("medium")
        f05 = model.longitudinal_force_n(0.05, 845.0, 1.0)
        f10 = model.longitudinal_force_n(0.10, 845.0, 1.0)
        f50 = model.longitudinal_force_n(0.50, 845.0, 1.0)
        assert f10 > f05
        # Force decreases in post-peak slip region
        assert f50 < f10

    def test_temp_factor_peaks_at_optimal(self):
        model = PacejkaTireModel("medium")
        tf_opt = model._temp_factor(model.opt_temp)
        tf_cold = model._temp_factor(model.opt_temp - 30)
        tf_hot = model._temp_factor(model.opt_temp + 40)
        assert tf_opt == pytest.approx(1.0, abs=1e-9)
        assert tf_cold < tf_opt
        assert tf_hot < tf_opt

    def test_mu_peak_drops_progressively_with_wear(self):
        model = PacejkaTireModel("medium")
        t = model.opt_temp
        mu0 = model.mu_peak(0.0, t)
        mu30 = model.mu_peak(30.0, t)   # boundary: grip unchanged at exactly 30 %
        mu50 = model.mu_peak(50.0, t)
        mu70 = model.mu_peak(70.0, t)
        mu90 = model.mu_peak(90.0, t)
        # At 30 % wear the penalty has not yet started (threshold is < 30 %)
        assert mu0 >= mu30
        # Above 30 % wear: progressive grip drop
        assert mu30 > mu50 > mu70 > mu90

    def test_soft_has_higher_peak_than_hard(self):
        soft = PacejkaTireModel("soft")
        hard = PacejkaTireModel("hard")
        mu_soft = soft.mu_peak(0.0, soft.opt_temp)
        mu_hard = hard.mu_peak(0.0, hard.opt_temp)
        assert mu_soft > mu_hard

    def test_wear_increment_positive(self):
        model = PacejkaTireModel("medium")
        from digital_twin_lab.tire.pacejka_model import _BIKE_MASS_KG, _G, _REAR_WEIGHT_FRACTION
        rear_load = _BIKE_MASS_KG * _G * _REAR_WEIGHT_FRACTION
        inc = model._wear_increment_pct(rear_load, 52.0, 0.68, 0.74, 98.0)
        assert inc > 0.0
        assert 0.5 < inc < 3.0  # MotoGP medium: ~1.5 %/lap at race conditions


class TestStintSimulation:
    def test_stint_returns_correct_lap_count(self):
        model = PacejkaTireModel("medium")
        result = model.simulate_stint(laps=15, circuit_profile=_JEREZ)
        assert isinstance(result, StintSimResult)
        assert len(result.laps) == 15
        assert all(isinstance(s, TireLapState) for s in result.laps)

    def test_wear_is_monotonically_increasing(self):
        model = PacejkaTireModel("medium")
        result = model.simulate_stint(laps=20, circuit_profile=_JEREZ)
        wears = [s.wear_pct for s in result.laps]
        assert all(wears[i] <= wears[i + 1] for i in range(len(wears) - 1))

    def test_grip_factor_between_zero_and_one(self):
        model = PacejkaTireModel("soft")
        result = model.simulate_stint(laps=25, circuit_profile=_JEREZ, ambient_temp_c=35.0)
        for state in result.laps:
            assert 0.0 <= state.grip_factor <= 1.0, f"grip_factor out of range: {state.grip_factor}"

    def test_soft_degrades_faster_than_hard(self):
        circuit = _JEREZ
        soft = PacejkaTireModel("soft").simulate_stint(30, circuit_profile=circuit)
        hard = PacejkaTireModel("hard").simulate_stint(30, circuit_profile=circuit)
        soft_final_wear = soft.laps[-1].wear_pct
        hard_final_wear = hard.laps[-1].wear_pct
        assert soft_final_wear > hard_final_wear

    def test_cliff_lap_is_within_stint_range(self):
        model = PacejkaTireModel("soft")
        result = model.simulate_stint(laps=30, circuit_profile=_JEREZ, ambient_temp_c=38.0)
        assert 1 <= result.cliff_lap <= 30

    def test_high_thermal_load_increases_wear(self):
        hot_circuit = dict(_JEREZ, thermal_load=0.92)
        cool_circuit = dict(_JEREZ, thermal_load=0.35)
        model = PacejkaTireModel("medium")
        hot = model.simulate_stint(15, circuit_profile=hot_circuit)
        cool = model.simulate_stint(15, circuit_profile=cool_circuit)
        assert hot.laps[-1].wear_pct > cool.laps[-1].wear_pct


class TestCollapsePredictor:
    def test_collapse_predicted_for_highly_worn_tyre(self):
        model = PacejkaTireModel("soft")
        result = model.predict_collapse(
            current_wear_pct=75.0,
            current_temp_c=135.0,
            remaining_laps=10,
            circuit_profile=_JEREZ,
            ambient_temp_c=30.0,
        )
        assert result["collapse_predicted"] is True
        assert result["risk_level"] in ("medium", "high")

    def test_no_collapse_for_fresh_tyre(self):
        model = PacejkaTireModel("hard")
        result = model.predict_collapse(
            current_wear_pct=5.0,
            current_temp_c=105.0,
            remaining_laps=5,
            circuit_profile=_JEREZ,
            ambient_temp_c=25.0,
        )
        assert result["risk_level"] in ("low", "medium-low")
        assert result["remaining_laps_safe"] >= 1

    def test_degradation_index_in_range(self):
        model = PacejkaTireModel("medium")
        result = model.predict_collapse(
            current_wear_pct=40.0,
            current_temp_c=100.0,
            remaining_laps=8,
            circuit_profile=_JEREZ,
        )
        assert 0.0 <= result["degradation_index"] <= 1.0
