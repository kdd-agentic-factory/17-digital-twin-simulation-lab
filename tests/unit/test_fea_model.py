"""Tests for the analytical FEM/FEA structural model — §8.3."""

from __future__ import annotations

import math

import pytest

from digital_twin_lab.parts import fea_model as fea


def test_cantilever_bending_matches_closed_form():
    # Solid round bar, d=20mm, bending moment 100 Nm.
    d = 20.0 / 1000.0
    I = math.pi * d**4 / 64.0
    expected_mpa = (100.0 * (d / 2) / I) * 1e-6
    res = fea.run_fea("steel_4340", {"type": "solid_round", "d": 20}, {"bending_moment_Nm": 100})
    assert res["stresses_mpa"]["bending"] == pytest.approx(expected_mpa, rel=1e-3)
    assert res["governing_mode"] == "bending"


def test_strong_part_passes_weak_part_fails():
    strong = fea.run_fea("ti_6al4v", {"type": "tube", "od": 30, "id": 20}, {"bending_moment_Nm": 150})
    weak = fea.run_fea("magnesium_az80", {"type": "solid_round", "d": 8}, {"bending_moment_Nm": 150})
    assert strong["safety_factor"] > weak["safety_factor"]
    assert strong["verdict"] == "pass"
    assert weak["verdict"] == "fail"


def test_thermal_derating_lowers_safety_factor():
    cold = fea.run_fea("alu_7075_t6", {"type": "solid_round", "d": 15}, {"bending_moment_Nm": 60}, operating_temp_c=20)
    hot = fea.run_fea("alu_7075_t6", {"type": "solid_round", "d": 15}, {"bending_moment_Nm": 60}, operating_temp_c=180)
    assert hot["safety_factor"] < cold["safety_factor"]
    assert hot["thermal_limited"] is True
    assert hot["yield_effective_mpa"] < cold["yield_effective_mpa"]


def test_pure_torsion_is_torsion_governed():
    res = fea.run_fea("steel_4340", {"type": "tube", "od": 25, "id": 20}, {"torque_Nm": 200})
    assert res["governing_mode"] == "torsion"
    assert res["stresses_mpa"]["torsional_shear"] > 0


def test_unknown_material_and_section_raise():
    with pytest.raises(ValueError):
        fea.run_fea("unobtanium", {"type": "solid_round", "d": 10}, {"bending_moment_Nm": 10})
    with pytest.raises(ValueError):
        fea.run_fea("steel_4340", {"type": "hexagon", "a": 10}, {"bending_moment_Nm": 10})
    with pytest.raises(ValueError):
        fea.run_fea("steel_4340", {"type": "tube", "od": 20, "id": 25}, {"torque_Nm": 10})
