"""Tests for the PINN Magic-Formula estimator (§14.2). Skipped without torch."""

from __future__ import annotations

import numpy as np
import pytest

from digital_twin_lab.tire import pinn_magic_formula as pinn

pytestmark = pytest.mark.skipif(not pinn.torch_available(), reason="torch not installed")

# Ground-truth medium-compound coefficients (from PacejkaTireModel).
_TRUE = {"B": 10.0, "C": 1.55, "D": 1.35, "E": -0.40}


def _synth_samples(n: int = 120, seed: int = 0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        kappa = float(rng.uniform(-0.2, 0.2))
        load = float(rng.uniform(700, 1000))
        temp = float(rng.uniform(85, 115))
        f_norm = pinn._magic_np(np.array([kappa]), **_TRUE)[0]
        force = f_norm * load + rng.normal(0, 0.01) * load
        out.append({"slip_ratio": kappa, "normal_load_n": load, "temp_c": temp, "force_n": float(force)})
    return out


def test_recovers_coefficients_within_guard():
    res = pinn.fit_and_predict(_synth_samples(), {"normal_load_n": 850, "temp_c": 100}, epochs=400)
    c = res["coefficients"]
    # all coefficients respect the Physics Guard bounds
    for k, (lo, hi) in pinn.GUARD.items():
        assert lo <= c[k] <= hi
    # good physical fit + recovered peak friction near ground truth
    assert res["fit_rmse_normalised"] < 0.05
    assert abs(res["mu_peak"] - _TRUE["D"]) < 0.25
    assert len(res["force_curve_normalised"]) == 21


def test_physics_guard_bounds_present():
    res = pinn.fit_and_predict(_synth_samples(60), {"normal_load_n": 800, "temp_c": 95}, epochs=50)
    assert res["physics_guard_bounds"]["D"] == pinn.GUARD["D"]
