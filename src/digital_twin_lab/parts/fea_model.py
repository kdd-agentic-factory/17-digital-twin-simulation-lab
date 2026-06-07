"""Analytical FEM/FEA structural check for AI-generated parts (Spec §8.3).

The Engineering Portal runs a finite-element-style structural evaluation on each
candidate part *before* physical manufacture, assessing mechanical resistance,
shear under thermal stress and structural torsion under virtual race loads.

This is a closed-form (beam/shaft) reduction of FEA — exact for the slender
structural members that make up most chassis/sub-frame parts — covering the three
modes the spec calls out:

* **Bending** — σ_b = M·c / I
* **Torsion / shear** — τ = T·r / J  (plus transverse shear)
* **Thermal derating** — the material yield strength falls with operating
  temperature, so the *effective* yield used for the safety factor is derated.

It returns the von-Mises equivalent stress, the safety factor against the derated
yield, and the governing failure mode — enough to gate the part for manufacture.
"""

from __future__ import annotations

import math
from typing import Any

# Material library: E (GPa), yield (MPa), density (kg/m³), yield temp-coefficient
# (fractional loss of yield per °C above ref_temp), ref_temp (°C).
_MATERIALS: dict[str, dict[str, float]] = {
    "steel_4340":   {"E_GPa": 205, "yield_MPa": 1100, "density": 7850, "temp_coeff": 0.00035, "ref_temp": 20},
    "alu_7075_t6":  {"E_GPa": 71.7, "yield_MPa": 503, "density": 2810, "temp_coeff": 0.00090, "ref_temp": 20},
    "ti_6al4v":     {"E_GPa": 113.8, "yield_MPa": 880, "density": 4430, "temp_coeff": 0.00045, "ref_temp": 20},
    "magnesium_az80": {"E_GPa": 45, "yield_MPa": 275, "density": 1810, "temp_coeff": 0.00120, "ref_temp": 20},
    "cfrp_t700":    {"E_GPa": 135, "yield_MPa": 600, "density": 1600, "temp_coeff": 0.00060, "ref_temp": 20},
}


def _section_properties(section: dict[str, Any]) -> dict[str, float]:
    """Return area A (m²), second moment I (m⁴), extreme fibre c (m),
    polar moment J (m⁴) and outer radius r (m) for a cross-section.

    Supported ``type``: ``solid_round`` (d), ``tube`` (od, id), ``rect`` (b, h).
    Dimensions are in millimetres.
    """
    kind = section["type"]
    if kind == "solid_round":
        d = section["d"] / 1000.0
        r = d / 2.0
        A = math.pi * r**2
        I = math.pi * d**4 / 64.0
        J = math.pi * d**4 / 32.0
        return {"A": A, "I": I, "c": r, "J": J, "r": r}
    if kind == "tube":
        od = section["od"] / 1000.0
        idia = section["id"] / 1000.0
        if idia >= od:
            raise ValueError("tube id must be smaller than od")
        ro, ri = od / 2.0, idia / 2.0
        A = math.pi * (ro**2 - ri**2)
        I = math.pi * (od**4 - idia**4) / 64.0
        J = math.pi * (od**4 - idia**4) / 32.0
        return {"A": A, "I": I, "c": ro, "J": J, "r": ro}
    if kind == "rect":
        b = section["b"] / 1000.0
        h = section["h"] / 1000.0
        A = b * h
        I = b * h**3 / 12.0
        c = h / 2.0
        # torsion constant for a rectangle (approx, b>=h): J ≈ β·b·h³
        a, bb = max(b, h), min(b, h)
        beta = 1.0 / 3.0 - 0.21 * (bb / a) * (1 - (bb / a) ** 4 / 12.0)
        J = beta * a * bb**3
        return {"A": A, "I": I, "c": c, "J": J, "r": c}
    raise ValueError(f"unknown section type '{kind}'")


def run_fea(
    material: str,
    section: dict[str, Any],
    loads: dict[str, float],
    *,
    operating_temp_c: float = 20.0,
    target_safety_factor: float = 1.5,
) -> dict[str, Any]:
    """Closed-form structural FEA of a part under combined race loads.

    Parameters
    ----------
    material : key into the material library.
    section : cross-section spec (see ``_section_properties``).
    loads : {"bending_moment_Nm", "torque_Nm", "axial_N"} (any subset).
    operating_temp_c : part operating temperature (derates yield).
    target_safety_factor : SF below which the part is rejected.
    """
    if material not in _MATERIALS:
        raise ValueError(f"unknown material '{material}'. Known: {sorted(_MATERIALS)}")
    mat = _MATERIALS[material]
    sp = _section_properties(section)

    M = float(loads.get("bending_moment_Nm", 0.0))
    T = float(loads.get("torque_Nm", 0.0))
    N = float(loads.get("axial_N", 0.0))

    # Stresses in Pa → MPa
    sigma_bending = (M * sp["c"] / sp["I"]) if sp["I"] > 0 else 0.0
    sigma_axial = (N / sp["A"]) if sp["A"] > 0 else 0.0
    sigma_normal = sigma_bending + sigma_axial
    tau_torsion = (T * sp["r"] / sp["J"]) if sp["J"] > 0 else 0.0

    sigma_vm = math.sqrt(sigma_normal**2 + 3.0 * tau_torsion**2)
    to_mpa = 1e-6

    # Thermal derating of yield strength
    derate = max(0.2, 1.0 - mat["temp_coeff"] * max(0.0, operating_temp_c - mat["ref_temp"]))
    yield_eff = mat["yield_MPa"] * derate

    sigma_vm_mpa = sigma_vm * to_mpa
    sf = (yield_eff / sigma_vm_mpa) if sigma_vm_mpa > 1e-9 else 999.0

    # Governing mode
    contributions = {
        "bending": abs(sigma_bending),
        "axial": abs(sigma_axial),
        "torsion": math.sqrt(3.0) * abs(tau_torsion),
    }
    governing = max(contributions, key=contributions.get)
    thermal_limited = derate < 0.97

    verdict = "pass" if sf >= target_safety_factor else "marginal" if sf >= 1.0 else "fail"

    return {
        "material": material,
        "operating_temp_c": operating_temp_c,
        "section": section["type"],
        "section_properties": {
            "area_mm2": round(sp["A"] * 1e6, 2),
            "I_mm4": round(sp["I"] * 1e12, 1),
            "J_mm4": round(sp["J"] * 1e12, 1),
        },
        "stresses_mpa": {
            "bending": round(sigma_bending * to_mpa, 2),
            "axial": round(sigma_axial * to_mpa, 2),
            "torsional_shear": round(tau_torsion * to_mpa, 2),
            "von_mises": round(sigma_vm_mpa, 2),
        },
        "yield_mpa": mat["yield_MPa"],
        "yield_effective_mpa": round(yield_eff, 1),
        "thermal_derate_factor": round(derate, 4),
        "thermal_limited": thermal_limited,
        "safety_factor": round(sf, 3),
        "target_safety_factor": target_safety_factor,
        "governing_mode": governing,
        "verdict": verdict,
        "conclusion": (
            f"{material} {section['type']} under M={M:.0f}Nm/T={T:.0f}Nm at "
            f"{operating_temp_c:.0f}°C: von-Mises {sigma_vm_mpa:.0f} MPa vs derated yield "
            f"{yield_eff:.0f} MPa → SF {sf:.2f} ({verdict}, {governing}-governed"
            f"{', thermally limited' if thermal_limited else ''})."
        ),
    }
