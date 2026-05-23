from __future__ import annotations


class CornerPhaseModel:
    """Assigns entry/apex/exit emphasis for corner segments."""

    def describe(self, corner: dict[str, object]) -> dict[str, float | str]:
        speed = float(corner.get("avg_speed_kph", 120.0))
        return {
            "corner_id": str(corner.get("corner_id", "unknown")),
            "entry_weight": round(min(0.55, 0.3 + speed / 600.0), 3),
            "apex_weight": 0.25,
            "exit_weight": round(max(0.2, 0.45 - speed / 700.0), 3),
        }
