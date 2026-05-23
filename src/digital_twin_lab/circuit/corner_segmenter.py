from __future__ import annotations


class CornerSegmenter:
    """Builds lightweight corner segments from circuit profile data."""

    def segment(self, circuit_profile: dict[str, object]) -> list[dict[str, object]]:
        corners = circuit_profile.get("corners") or []
        if corners:
            return [dict(corner) for corner in corners]
        circuit_id = str(circuit_profile.get("circuit_id", "track"))
        return [
            {"corner_id": f"{circuit_id}-sector-1", "type": "mixed", "avg_speed_kph": 135.0},
            {"corner_id": f"{circuit_id}-sector-2", "type": "mixed", "avg_speed_kph": 118.0},
        ]
