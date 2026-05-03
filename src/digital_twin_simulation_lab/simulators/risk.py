from digital_twin_simulation_lab.domain import RiskLevel


def classify_risk(temp_delta_c: float, spin_delta_pct: float, lap_delta_s: float) -> RiskLevel:
    if temp_delta_c > 6.0 or spin_delta_pct > 8.0 or lap_delta_s > 0.18:
        return "high"
    if temp_delta_c > 2.5 or spin_delta_pct > 3.0 or lap_delta_s > 0.10:
        return "medium"
    if temp_delta_c < -1.0 and spin_delta_pct < -2.0 and lap_delta_s <= 0.08:
        return "medium-low"
    return "low"
