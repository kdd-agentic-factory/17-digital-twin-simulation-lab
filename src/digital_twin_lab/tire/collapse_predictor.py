from __future__ import annotations


class CollapsePredictor:
    """Converts degradation index into a collapse projection."""

    def predict(self, *, degradation_index: float, stint_laps: int) -> dict[str, int | bool]:
        predicted_lap = max(1, int((1.02 - degradation_index) * stint_laps))
        return {
            "will_collapse": degradation_index >= 0.82 or predicted_lap <= stint_laps,
            "predicted_lap": predicted_lap,
        }
