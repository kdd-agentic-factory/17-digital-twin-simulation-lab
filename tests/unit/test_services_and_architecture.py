from importlib import import_module

from digital_twin_lab.models.scenario import SimulationScenario
from digital_twin_lab.models.simulation import SimulationRequest
from digital_twin_lab.services.report_service import ReportService
from digital_twin_lab.services.scenario_service import ScenarioService
from digital_twin_lab.services.simulation_service import SimulationService


def test_specification_architecture_modules_are_importable():
    module_names = [
        "digital_twin_lab.simulation",
        "digital_twin_lab.simulation.scenario_runner",
        "digital_twin_lab.simulation.simulation_engine",
        "digital_twin_lab.simulation.baseline_comparator",
        "digital_twin_lab.simulation.monte_carlo_runner",
        "digital_twin_lab.simulation.sensitivity_analyzer",
        "digital_twin_lab.simulation.uncertainty_estimator",
        "digital_twin_lab.simulation.result_builder",
        "digital_twin_lab.models.telemetry",
        "digital_twin_lab.vehicle.simplified_vehicle_model",
        "digital_twin_lab.vehicle.longitudinal_model",
        "digital_twin_lab.vehicle.lateral_model",
        "digital_twin_lab.vehicle.load_transfer_model",
        "digital_twin_lab.vehicle.suspension_model",
        "digital_twin_lab.vehicle.engine_map_model",
        "digital_twin_lab.tire.tire_degradation_model",
        "digital_twin_lab.tire.tire_thermal_model",
        "digital_twin_lab.tire.spin_model",
        "digital_twin_lab.tire.grip_model",
        "digital_twin_lab.tire.collapse_predictor",
        "digital_twin_lab.circuit.corner_segmenter",
        "digital_twin_lab.circuit.corner_phase_model",
        "digital_twin_lab.circuit.track_risk_model",
    ]

    for module_name in module_names:
        assert import_module(module_name)


def test_simulation_service_runs_real_runner_and_report_service_tracks_latest_result():
    scenario = SimulationScenario(
        scenario_id="service-smoke-jerez",
        name="Service smoke",
        scenario_type="setup_change",
        circuit_id="jerez",
        session_id="race",
        baseline_setup_id="jerez-baseline",
        lap_range=(1, 10),
        metadata={
            "proposed_setup": {
                "front_rebound": 9,
                "rear_rebound": 11,
                "rear_ride_height_mm": 47,
                "engine_map": "mapping_2",
            },
            "ambient_temp_c": 31.0,
            "track_temp_c": 41.0,
            "laps": 10,
        },
    )

    simulation_result = SimulationService().run(
        SimulationRequest(scenario_id=scenario.scenario_id, iterations=3, use_real_time_data=True),
        scenario,
    )

    assert simulation_result.scenario_id == scenario.scenario_id
    assert simulation_result.summary.lap_time_delta_s < 0
    assert any("Iterations requested: 3." == item for item in simulation_result.evidence)
    assert any("Real-time data flag enabled" in item for item in simulation_result.evidence)

    latest_report = ReportService().generate_latest_report(simulation_result, scenario)

    assert latest_report.scenario_id == scenario.scenario_id
    assert ReportService().get_latest_report().report_id == latest_report.report_id


def test_scenario_service_exposes_catalog_backed_listing_and_lookup():
    service = ScenarioService()

    items = service.list_scenarios()
    scenario = service.get_scenario("jerez-map2-rebound")

    assert items
    assert any(item["scenario_id"] == "jerez-map2-rebound" for item in items)
    assert scenario.scenario_id == "jerez-map2-rebound"
    assert scenario.metadata["proposed_setup"]["engine_map"] == "mapping_2"
