"""Setup validation orchestration."""

from __future__ import annotations

from digital_twin_lab.circuit.circuit_profile_loader import CircuitProfileLoader
from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.models.setup import SetupChange


class SetupValidationService:
    """Validates setup changes before dispatching them to simulation."""

    VALID_PARAMETERS = {
        "rear_rebound",
        "front_rebound",
        "rear_pressure",
        "front_pressure",
        "engine_map",
        "aero_package",
    }

    def __init__(self, circuit_loader: CircuitProfileLoader | None = None) -> None:
        self.circuit_loader = circuit_loader or CircuitProfileLoader()

    def validate(self, scenario: SimulationScenario) -> dict[str, object]:
        """Validate a scenario and its setup change into an API-friendly payload."""
        issues: list[str] = []
        warnings: list[str] = []

        if scenario.setup_change is not None:
            issues.extend(self._validate_setup_change(scenario.setup_change))
        else:
            warnings.append("Scenario does not include an explicit setup change.")

        start_lap, end_lap = scenario.lap_range
        if start_lap > end_lap:
            issues.append("lap_range start must be less than or equal to lap_range end.")

        try:
            profile = self.circuit_loader.load_profile(scenario.circuit_id)
            available_corner_ids = {corner.corner_id for corner in profile.corners}
            missing = [corner_id for corner_id in scenario.corner_ids if corner_id not in available_corner_ids]
            if missing:
                warnings.append(f"Unknown corner ids for circuit {scenario.circuit_id}: {missing}.")
        except FileNotFoundError:
            warnings.append(f"Circuit profile '{scenario.circuit_id}' not found; skipping corner validation.")
        except ValueError as exc:
            warnings.append(f"Circuit profile could not be parsed: {exc}")

        return {
            "scenario_id": scenario.scenario_id,
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "ready_for_simulation": not issues,
        }

    def _validate_setup_change(self, setup_change: SetupChange) -> list[str]:
        issues: list[str] = []
        parameter = setup_change.parameter_name.lower()
        if parameter not in self.VALID_PARAMETERS:
            issues.append(f"Unsupported setup parameter '{setup_change.parameter_name}'.")

        if parameter.endswith("pressure"):
            delta = float(setup_change.new_value) - float(setup_change.old_value)
            if abs(delta) > 0.30:
                issues.append("Pressure delta is too large for lightweight validation limits (max 0.30 bar).")

        if parameter.endswith("rebound") and abs(int(setup_change.new_value)) > 8:
            issues.append("Rebound change exceeds the placeholder validation window of +/- 8 clicks.")

        return issues
