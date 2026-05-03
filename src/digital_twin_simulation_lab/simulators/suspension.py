def rear_rebound_effect(clicks: int) -> dict[str, float]:
    """Estimate rear rebound impact around corner exit traction."""
    bounded_clicks = max(-4, min(4, clicks))
    return {
        "spin_delta_pct": -1.4 * bounded_clicks,
        "temp_delta_c": -0.75 * bounded_clicks,
        "lap_penalty_s": 0.005 * abs(bounded_clicks),
    }
