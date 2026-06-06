"""Physics-Informed Neural Network for the Pacejka Magic Formula (Spec §14.2).

Estimates the Pacejka tyre coefficients (B, C, D, E) as functions of the
operating conditions (normal load, carcass temperature) from observed tyre
forces. The physics is *baked in*: the network never predicts force directly —
it predicts the four Magic-Formula coefficients, and the force is evaluated
through the actual Pacejka formula

    f(κ) = D · sin(C · atan(B·κ − E·(B·κ − atan(B·κ))))   (force normalised by load)

so the fit stays physically meaningful (this is the "physics-informed" part).

The **Physics Guard** is built into the architecture: the raw network outputs are
squashed (sigmoid) into physically-plausible coefficient ranges spanning the
soft/medium/hard compounds, so the model can never emit an impossible tyre.

``torch`` is imported lazily (the rest of the service runs without it; the
runtime image installs the CPU build).
"""

from __future__ import annotations

from typing import Any

import numpy as np

# Physics-Guard coefficient bounds (span soft/medium/hard + margin).
GUARD = {
    "B": (6.0, 16.0),    # stiffness factor
    "C": (1.30, 1.80),   # shape factor
    "D": (0.85, 1.65),   # peak friction coefficient μ (force normalised by load)
    "E": (-1.00, 0.20),  # curvature factor
}


def torch_available() -> bool:
    try:
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def _magic_np(kappa: np.ndarray, B: float, C: float, D: float, E: float) -> np.ndarray:
    inner = B * kappa - E * (B * kappa - np.arctan(B * kappa))
    return D * np.sin(C * np.arctan(inner))


def fit_and_predict(
    samples: list[dict[str, float]],
    query: dict[str, float],
    *,
    epochs: int = 300,
    seed: int = 0,
) -> dict[str, Any]:
    """Fit the PINN on observed (slip, load, temp, force) and predict coefficients.

    Each sample: ``slip_ratio``, ``normal_load_n``, ``temp_c``, ``force_n``.
    ``query``: ``normal_load_n``, ``temp_c`` — the condition to estimate for.
    """
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    np.random.seed(seed)

    slip = np.array([s["slip_ratio"] for s in samples], dtype=np.float32)
    load = np.array([s["normal_load_n"] for s in samples], dtype=np.float32)
    temp = np.array([s["temp_c"] for s in samples], dtype=np.float32)
    force = np.array([s["force_n"] for s in samples], dtype=np.float32)
    f_norm = force / np.maximum(load, 1.0)            # normalise force by load

    # Standardise the conditioning inputs (load, temp).
    cond = np.stack([load, temp], axis=1)
    c_mu, c_sd = cond.mean(0), cond.std(0) + 1e-6
    cond_s = (cond - c_mu) / c_sd

    slip_t = torch.tensor(slip).unsqueeze(1)
    cond_t = torch.tensor(cond_s)
    fnorm_t = torch.tensor(f_norm).unsqueeze(1)

    lo = torch.tensor([GUARD[k][0] for k in ("B", "C", "D", "E")])
    hi = torch.tensor([GUARD[k][1] for k in ("B", "C", "D", "E")])

    class PINN(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(2, 24), nn.Tanh(), nn.Linear(24, 24), nn.Tanh(), nn.Linear(24, 4))

        def coeffs(self, cond):
            # Physics Guard: squash to plausible ranges → cannot emit an impossible tyre.
            return lo + (hi - lo) * torch.sigmoid(self.net(cond))

        def forward(self, cond, kappa):
            c = self.coeffs(cond)
            B, C, D, E = c[:, 0:1], c[:, 1:2], c[:, 2:3], c[:, 3:4]
            inner = B * kappa - E * (B * kappa - torch.atan(B * kappa))
            return D * torch.sin(C * torch.atan(inner)), c

    model = PINN()
    opt = torch.optim.Adam(model.parameters(), lr=5e-3)
    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        pred, _ = model(cond_t, slip_t)
        loss = nn.functional.mse_loss(pred, fnorm_t)
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        pred, _ = model(cond_t, slip_t)
        rmse = float(torch.sqrt(nn.functional.mse_loss(pred, fnorm_t)))
        q = torch.tensor(((np.array([[query["normal_load_n"], query["temp_c"]]]) - c_mu) / c_sd), dtype=torch.float32)
        qc = model.coeffs(q)[0].numpy()

    B, C, D, E = (float(qc[i]) for i in range(4))
    grid = np.linspace(-0.25, 0.25, 21)
    curve = _magic_np(grid, B, C, D, E)
    return {
        "coefficients": {"B": round(B, 4), "C": round(C, 4), "D": round(D, 4), "E": round(E, 4)},
        "mu_peak": round(D, 4),
        "query": query,
        "fit_rmse_normalised": round(rmse, 5),
        "physics_guard_bounds": GUARD,
        "force_curve_normalised": [
            {"slip": round(float(k), 3), "force_norm": round(float(f), 4)} for k, f in zip(grid, curve)
        ],
    }
