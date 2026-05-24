"""Pacejka Magic Formula tire model with Archard wear law and lumped-capacitance thermal model.

Physics basis:
  F = D * sin(C * arctan(B*κ - E*(B*κ - arctan(B*κ))))   [Pacejka '94]
  dW/ds = k_w * F_n / H_rubber                              [Archard wear]
  ΔT/lap = (Q_slip - Q_conv) / (m_tire * c_p)              [1st law, lumped]
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

CompoundType = Literal["soft", "medium", "hard"]

# Pacejka BCD coefficients + thermal / wear constants per compound.
# Calibrated for MotoGP rear tyre on dry asphalt (Michelin/Bridgestone range).
_COMPOUND: dict[str, dict] = {
    "soft": {
        "B": 12.0,   "C": 1.65,  "D": 1.45,  "E": -0.60,
        # k_wear: % wear per lap at reference conditions (847 N load, 250 m sliding)
        # MotoGP Michelin soft ≈ 2.5 %/lap at thermal_load 0.65, stability 0.74
        "k_wear": 2.5,
        "opt_temp_c": 90.0,
        "max_temp_c": 140.0,
        "temp_sigma": 22.0,
    },
    "medium": {
        "B": 10.0,   "C": 1.55,  "D": 1.35,  "E": -0.40,
        "k_wear": 1.5,             # ~1.5 %/lap at reference conditions
        "opt_temp_c": 100.0,
        "max_temp_c": 155.0,
        "temp_sigma": 25.0,
    },
    "hard": {
        "B": 8.5,    "C": 1.45,  "D": 1.22,  "E": -0.20,
        "k_wear": 0.85,            # ~0.85 %/lap at reference conditions
        "opt_temp_c": 110.0,
        "max_temp_c": 170.0,
        "temp_sigma": 28.0,
    },
}

# Physical constants
_BIKE_MASS_KG = 157.0
_REAR_WEIGHT_FRACTION = 0.55
_G = 9.81                   # m/s²
_TIRE_MASS_KG = 6.5
_C_P_RUBBER = 1_400.0       # J/(kg·K) — specific heat of rubber
_CONTACT_AREA_M2 = 0.018    # contact patch area
_H_CONV = 50.0              # W/(m²·K) — forced convection coefficient at ~150 km/h
_LAP_TIME_S_DEFAULT = 100.0 # fallback if not in circuit profile


@dataclass
class TireLapState:
    lap: int
    wear_pct: float        # 0 → fresh, 100 → fully worn
    carcass_temp_c: float
    grip_factor: float     # 1.0 = peak fresh-tyre grip
    mu_peak: float         # instantaneous Pacejka peak friction coefficient
    lap_time_delta_s: float  # extra seconds vs lap-1 fresh tyre
    spin_risk_pct: float   # 0-100 categorical risk indicator


@dataclass
class StintSimResult:
    compound: str
    laps: list[TireLapState] = field(default_factory=list)
    cliff_lap: int = 0     # lap at which wear >70 % or lap_delta >0.5 s


class PacejkaTireModel:
    """Lap-by-lap tyre simulation using the Pacejka Magic Formula.

    Usage::

        model = PacejkaTireModel("medium")
        result = model.simulate_stint(
            laps=20,
            circuit_profile={"base_lap_time_s": 98.2, "thermal_load": 0.68,
                             "stability_bias": 0.74, "avg_speed_ms": 52.0},
            ambient_temp_c=30.0,
        )
    """

    def __init__(self, compound: CompoundType = "medium") -> None:
        self.compound = compound
        p = _COMPOUND[compound]
        self.B = p["B"]
        self.C = p["C"]
        self.D_base = p["D"]
        self.E = p["E"]
        self.k_wear = p["k_wear"]  # %/lap at reference conditions
        self.opt_temp = p["opt_temp_c"]
        self.max_temp = p["max_temp_c"]
        self.temp_sigma = p["temp_sigma"]

    # ------------------------------------------------------------------
    # Pacejka Magic Formula
    # ------------------------------------------------------------------

    def _magic(self, x: float, D: float) -> float:
        """Evaluate the Magic Formula for a given slip input x and peak force D."""
        inner = self.B * x - self.E * (self.B * x - math.atan(self.B * x))
        return D * math.sin(self.C * math.atan(inner))

    def longitudinal_force_n(self, slip_ratio: float, normal_load_n: float, temp_factor: float) -> float:
        kappa = max(-1.0, min(1.0, slip_ratio))
        D = self.D_base * normal_load_n * temp_factor
        return self._magic(kappa, D)

    # ------------------------------------------------------------------
    # Derived quantities
    # ------------------------------------------------------------------

    def _temp_factor(self, temp_c: float) -> float:
        """Grip scale from tyre temperature — Gaussian bell curve around optimum."""
        return math.exp(-0.5 * ((temp_c - self.opt_temp) / self.temp_sigma) ** 2)

    def _wear_grip_penalty(self, wear_pct: float) -> float:
        """Progressive grip penalty with cliff onset above 70 % wear."""
        if wear_pct < 30.0:
            return 1.0
        if wear_pct < 70.0:
            return 1.0 - (wear_pct - 30.0) * 0.008  # −0.32 at 70 %
        # cliff region
        return max(0.30, 0.68 - (wear_pct - 70.0) * 0.019)

    def mu_peak(self, wear_pct: float, temp_c: float) -> float:
        """Instantaneous peak friction coefficient μ."""
        return self.D_base * self._temp_factor(temp_c) * self._wear_grip_penalty(wear_pct)

    # ------------------------------------------------------------------
    # Heat generation (Pacejka-derived)
    # ------------------------------------------------------------------

    def _heat_per_lap_j(
        self,
        rear_load_n: float,
        avg_speed_ms: float,
        thermal_load: float,
        stability_score: float,
        lap_time_s: float,
        temp_factor: float,
    ) -> float:
        """Energy dissipated by tyre slip per lap [J]."""
        # Average slip ratio driven by thermal load and stability
        avg_slip = 0.06 * thermal_load * (2.0 - stability_score)
        f_slip = self.longitudinal_force_n(avg_slip, rear_load_n, temp_factor)
        v_slip = avg_speed_ms * avg_slip
        return abs(f_slip * v_slip * lap_time_s)

    # ------------------------------------------------------------------
    # Archard wear law
    # ------------------------------------------------------------------

    # Reference conditions for wear normalisation
    _REF_LOAD_N: float = 847.0    # rear load at reference weight / distribution
    _REF_SLIDING_M: float = 250.0  # sliding distance per lap at thermal_load 0.65, stability 0.74

    def _wear_increment_pct(self, rear_load_n: float, avg_speed_ms: float, thermal_load: float, stability_score: float, lap_time_s: float) -> float:
        """Wear per lap in % — normalised Archard law.

        k_wear is in %/lap at reference conditions (_REF_LOAD_N load, _REF_SLIDING_M sliding).
        Scales with actual load and slip-energy relative to reference.
        """
        avg_slip = 0.06 * thermal_load * max(0.5, 2.0 - stability_score)
        sliding = avg_slip * avg_speed_ms * lap_time_s
        return self.k_wear * (rear_load_n / self._REF_LOAD_N) * (sliding / self._REF_SLIDING_M)

    # ------------------------------------------------------------------
    # Thermal model
    # ------------------------------------------------------------------

    def _delta_temp_c(
        self,
        heat_j: float,
        ambient_temp_c: float,
        current_temp_c: float,
    ) -> float:
        """ΔT per lap from lumped-capacitance thermal model."""
        m_cp = _TIRE_MASS_KG * _C_P_RUBBER
        q_conv_per_lap = _H_CONV * _CONTACT_AREA_M2 * max(0.0, current_temp_c - ambient_temp_c) * _LAP_TIME_S_DEFAULT
        net_heat = heat_j - q_conv_per_lap
        return net_heat / m_cp

    # ------------------------------------------------------------------
    # Stint simulation
    # ------------------------------------------------------------------

    def simulate_stint(
        self,
        laps: int,
        circuit_profile: dict,
        ambient_temp_c: float = 30.0,
        track_temp_c: float = 40.0,
        initial_temp_c: float | None = None,
        setup_stability_score: float = 0.75,
    ) -> StintSimResult:
        """Simulate a full tyre stint lap by lap.

        Returns a :class:`StintSimResult` with per-lap state and cliff lap index.
        """
        base_lap_s = float(circuit_profile.get("base_lap_time_s", _LAP_TIME_S_DEFAULT))
        thermal_load = float(circuit_profile.get("thermal_load", 0.65))
        avg_speed_ms = float(circuit_profile.get("avg_speed_ms", 50.0))
        stability_bias = float(circuit_profile.get("stability_bias", 0.74))
        effective_stability = min(1.0, (setup_stability_score + stability_bias) / 2.0)

        rear_load_n = _BIKE_MASS_KG * _G * _REAR_WEIGHT_FRACTION

        temp_c = initial_temp_c if initial_temp_c is not None else (ambient_temp_c + 62.0)
        wear_pct = 0.0
        fresh_mu = self.mu_peak(0.0, self.opt_temp)

        states: list[TireLapState] = []

        for lap in range(1, laps + 1):
            tf = self._temp_factor(temp_c)
            mu = self.mu_peak(wear_pct, temp_c)
            grip_factor = mu / fresh_mu if fresh_mu > 0 else 1.0

            # Lap time delta: grip loss drives time cost (0.035 s per 0.01 grip unit)
            grip_loss = max(0.0, fresh_mu - mu)
            lap_time_delta = grip_loss * 3.5

            # Spin risk — inversely proportional to grip_factor, amplified by thermal load
            spin_risk = min(100.0, max(0.0, (1.0 - grip_factor) * 70.0 + (thermal_load - 0.5) * 25.0))

            # Archard wear
            wear_pct = min(100.0, wear_pct + self._wear_increment_pct(rear_load_n, avg_speed_ms, thermal_load, effective_stability, base_lap_s))

            # Thermal update — use damping factor 0.08 to reflect gradual equilibration
            heat_j = self._heat_per_lap_j(rear_load_n, avg_speed_ms, thermal_load, effective_stability, base_lap_s, tf)
            dt = self._delta_temp_c(heat_j, ambient_temp_c, temp_c)
            temp_c = max(ambient_temp_c + 45.0, min(self.max_temp, temp_c + dt * 0.08))

            states.append(TireLapState(
                lap=lap,
                wear_pct=round(wear_pct, 2),
                carcass_temp_c=round(temp_c, 1),
                grip_factor=round(grip_factor, 4),
                mu_peak=round(mu, 4),
                lap_time_delta_s=round(lap_time_delta, 3),
                spin_risk_pct=round(spin_risk, 1),
            ))

        cliff_lap = laps
        for i, s in enumerate(states):
            if s.wear_pct > 70.0 or s.lap_time_delta_s > 0.5:
                cliff_lap = i + 1
                break

        return StintSimResult(compound=self.compound, laps=states, cliff_lap=cliff_lap)

    def predict_collapse(
        self,
        current_wear_pct: float,
        current_temp_c: float,
        remaining_laps: int,
        circuit_profile: dict,
        ambient_temp_c: float = 30.0,
        setup_stability_score: float = 0.75,
    ) -> dict:
        """Predict tyre collapse risk for the remaining laps of a stint."""
        base_lap_s = float(circuit_profile.get("base_lap_time_s", _LAP_TIME_S_DEFAULT))
        thermal_load = float(circuit_profile.get("thermal_load", 0.65))
        avg_speed_ms = float(circuit_profile.get("avg_speed_ms", 50.0))
        rear_load_n = _BIKE_MASS_KG * _G * _REAR_WEIGHT_FRACTION

        temp_c = current_temp_c
        wear_pct = current_wear_pct
        fresh_mu = self.mu_peak(0.0, self.opt_temp)
        collapse_lap: int | None = None

        for lap in range(1, remaining_laps + 1):
            wear_pct = min(100.0, wear_pct + self._wear_increment_pct(rear_load_n, avg_speed_ms, thermal_load, setup_stability_score, base_lap_s))
            heat_j = self._heat_per_lap_j(rear_load_n, avg_speed_ms, thermal_load, setup_stability_score, base_lap_s, self._temp_factor(temp_c))
            temp_c = max(ambient_temp_c + 40.0, min(self.max_temp, temp_c + self._delta_temp_c(heat_j, ambient_temp_c, temp_c) * 0.08))
            mu = self.mu_peak(wear_pct, temp_c)
            grip_factor = mu / fresh_mu if fresh_mu > 0 else 1.0
            if grip_factor < 0.65 or wear_pct > 85.0:
                collapse_lap = lap
                break

        final_mu = self.mu_peak(wear_pct, temp_c)
        degradation_index = 1.0 - (final_mu / fresh_mu) if fresh_mu > 0 else 1.0

        if collapse_lap is not None:
            risk_level = "high"
        elif degradation_index > 0.25:
            risk_level = "medium"
        elif degradation_index > 0.12:
            risk_level = "medium-low"
        else:
            risk_level = "low"

        return {
            "compound": self.compound,
            "collapse_predicted": collapse_lap is not None,
            "collapse_lap": collapse_lap,
            "remaining_laps_safe": (collapse_lap - 1) if collapse_lap else remaining_laps,
            "final_wear_pct": round(wear_pct, 2),
            "final_temp_c": round(temp_c, 1),
            "degradation_index": round(degradation_index, 4),
            "risk_level": risk_level,
        }
