from __future__ import annotations


class TrackRiskModel:
    """Produces a coarse track-risk summary from circuit metadata."""

    def assess(self, circuit_profile: dict[str, object], corners: list[dict[str, object]]) -> dict[str, object]:
        thermal_load = float(circuit_profile.get("thermal_load", 0.5))
        hottest_corner = max(corners, key=lambda corner: float(corner.get("avg_speed_kph", 0.0))) if corners else None
        return {
            "thermal_load": thermal_load,
            "highest_risk_corner_id": hottest_corner.get("corner_id") if hottest_corner else None,
            "risk_score": round(min(1.0, thermal_load * 0.65 + len(corners) * 0.04), 3),
        }
