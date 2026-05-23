from __future__ import annotations

from digital_twin_lab.circuit.corner_phase_model import CornerPhaseModel
from digital_twin_lab.circuit.corner_segmenter import CornerSegmenter
from digital_twin_lab.circuit.track_risk_model import TrackRiskModel
from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.models.telemetry import TelemetrySnapshot
from digital_twin_lab.services.what_if_service import WhatIfService
from digital_twin_lab.simulation.baseline_comparator import BaselineComparator
from digital_twin_lab.simulation.monte_carlo_runner import MonteCarloRunner
from digital_twin_lab.simulation.result_builder import EngineSimulationResult, ResultBuilder
from digital_twin_lab.simulation.sensitivity_analyzer import SensitivityAnalyzer
from digital_twin_lab.simulation.uncertainty_estimator import UncertaintyEstimator
from digital_twin_lab.tire.tire_degradation_model import TireDegradationModel
from digital_twin_lab.vehicle.simplified_vehicle_model import SimplifiedVehicleModel


class SimulationEngine:
    """Thin orchestration layer that converts MVP heuristics into spec-aligned results."""

    def __init__(self, what_if_service: WhatIfService | None = None) -> None:
        self._what_if_service = what_if_service or WhatIfService()
        self._vehicle = SimplifiedVehicleModel()
        self._segmenter = CornerSegmenter()
        self._corner_phase_model = CornerPhaseModel()
        self._track_risk_model = TrackRiskModel()
        self._comparator = BaselineComparator()
        self._monte_carlo = MonteCarloRunner()
        self._uncertainty = UncertaintyEstimator()
        self._sensitivity = SensitivityAnalyzer()
        self._degradation = TireDegradationModel()
        self._results = ResultBuilder()

    def run(self, scenario: SimulationScenario, *, iterations: int) -> EngineSimulationResult:
        metadata = dict(scenario.metadata)
        proposed_setup = metadata.get("proposed_setup", {})
        ambient_temp_c = float(metadata.get("ambient_temp_c", 30.0))
        track_temp_c = float(metadata.get("track_temp_c", 40.0))
        laps = int(metadata.get("laps", scenario.lap_range[1] - scenario.lap_range[0] + 1))
        simulation = self._what_if_service.simulate(
            scenario_id=scenario.scenario_id,
            circuit_id=scenario.circuit_id,
            baseline_setup_id=scenario.baseline_setup_id,
            proposed_setup=proposed_setup,
            ambient_temp_c=ambient_temp_c,
            track_temp_c=track_temp_c,
            laps=laps,
        )
        circuit_profile = self._what_if_service.load_circuit_profile(scenario.circuit_id)
        corners = self._segmenter.segment(circuit_profile)
        corner_phases = [self._corner_phase_model.describe(corner) for corner in corners]
        track_risk = self._track_risk_model.assess(circuit_profile, corners)
        comparator = self._comparator.compare(
            baseline_metrics=simulation["baseline_metrics"],
            proposed_metrics=simulation["proposed_metrics"],
            delta_metrics=simulation["delta_metrics"],
        )
        monte_carlo = self._monte_carlo.run(lap_time_delta_s=float(simulation["delta_metrics"]["lap_time_delta_s"]), iterations=iterations)
        uncertainty = self._uncertainty.estimate(monte_carlo)
        sensitivity = self._sensitivity.analyze(simulation["changed_parameters"])
        vehicle_window = self._vehicle.evaluate_setup_window(
            engine_map=str(proposed_setup.get("engine_map", "mapping_1")),
            rear_rebound=float(proposed_setup.get("rear_rebound", 10)),
            rear_ride_height_mm=float(proposed_setup.get("rear_ride_height_mm", 45)),
        )
        degradation_delay = self._degradation.estimate_degradation_delay(
            temp_delta_c=float(simulation["delta_metrics"]["rear_temp_delta_c"]),
            spin_delta_pct=min(0.0, float(simulation["delta_metrics"]["stability_score_delta"]) * 10.0),
        )
        telemetry = TelemetrySnapshot(
            speed_kph=round(190.0 * vehicle_window["torque_factor"], 3),
            rear_carcass_temp_c=simulation["proposed_metrics"]["rear_temp_c"],
            rear_spin_pct=max(0.0, -float(simulation["delta_metrics"]["stability_score_delta"]) * 25.0),
            lean_angle_deg=52.0,
        )
        evidence = [
            simulation["explanation"],
            f"Changed parameters ranked by sensitivity: {', '.join(sensitivity) or 'none'}.",
            f"Track highest risk corner: {track_risk['highest_risk_corner_id']} (score {track_risk['risk_score']}).",
            f"Monte Carlo spread: {monte_carlo['lap_time_min_s']} to {monte_carlo['lap_time_max_s']} s over {iterations} iterations.",
            f"Telemetry proxy: {telemetry.speed_kph} kph, rear carcass {telemetry.rear_carcass_temp_c} C.",
        ]
        return self._results.build(
            scenario_id=scenario.scenario_id,
            risk=str(simulation["risk_level"]),
            lap_time_delta_s=float(simulation["delta_metrics"]["lap_time_delta_s"]),
            stability_score_delta=float(simulation["delta_metrics"]["stability_score_delta"]),
            rear_temp_delta_c=float(simulation["delta_metrics"]["rear_temp_delta_c"]),
            degradation_delay_laps=degradation_delay,
            evidence=evidence,
            artifacts={
                "comparison": comparator,
                "corner_phases": corner_phases,
                "track_risk": track_risk,
                "monte_carlo": monte_carlo,
                "uncertainty": uncertainty,
                "vehicle_window": vehicle_window,
            },
        )
