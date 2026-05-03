from digital_twin_simulation_lab.domain import BaselineTelemetry, SetupChanges, SimulationScenario
from digital_twin_simulation_lab.simulators import run_what_if


def test_mapping_2_and_rebound_reduce_spin_and_temperature():
    scenario = SimulationScenario(
        scenario_id="qatar-race-l10-map2-rebound",
        circuit="Losail",
        session="race",
        base_lap_time_s=113.42,
        laps=22,
        changes=SetupChanges(
            rear_rebound_clicks=2,
            engine_map="mapping_2",
            apply_from_lap=10,
        ),
        baseline=BaselineTelemetry(
            rear_carcass_temp_c=112.0,
            rear_pressure_bar=1.72,
            spin_t05_pct=18.0,
        ),
    )

    result = run_what_if(scenario)

    assert result.summary.spin_t05_delta_pct == -7.8
    assert result.summary.rear_carcass_temp_delta_c == -4.2
    assert result.summary.lap_time_delta_s == 0.04
    assert result.summary.degradation_delay_laps == 3
    assert result.risk == "medium-low"


def test_front_pressure_aero_and_mapping_1_increase_risk_factors():
    scenario = SimulationScenario(
        scenario_id="riskier-map1-low-drag",
        circuit="Losail",
        session="fp2",
        base_lap_time_s=113.42,
        laps=18,
        changes=SetupChanges(
            front_pressure_delta_bar=0.10,
            engine_map="mapping_1",
            aero_package="low_drag",
            apply_from_lap=3,
        ),
        baseline=BaselineTelemetry(
            rear_carcass_temp_c=108.0,
            rear_pressure_bar=1.70,
            spin_t05_pct=15.0,
        ),
    )

    result = run_what_if(scenario)

    assert result.summary.spin_t05_delta_pct > 0
    assert result.summary.rear_carcass_temp_delta_c > 0
    assert result.risk in {"medium", "high"}
