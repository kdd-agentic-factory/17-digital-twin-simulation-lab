from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SetupDiff:
    changed_parameters: dict[str, dict[str, object]]

    @classmethod
    def from_setups(cls, *, baseline: dict[str, object], proposed: dict[str, object]) -> "SetupDiff":
        changed: dict[str, dict[str, object]] = {}
        for key, proposed_value in proposed.items():
            baseline_value = baseline.get(key)
            if baseline_value == proposed_value:
                continue
            if isinstance(baseline_value, (int, float)) and isinstance(proposed_value, (int, float)):
                delta: object = proposed_value - baseline_value
            else:
                delta = proposed_value
            changed[key] = {"baseline": baseline_value, "proposed": proposed_value, "delta": delta}
        return cls(changed_parameters=changed)
