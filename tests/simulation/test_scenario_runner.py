from pathlib import Path

from digital_twin_simulation_lab.scenario_runner import load_scenario
from digital_twin_simulation_lab.simulators import run_what_if


def test_sample_race_scenario_can_be_loaded_and_run():
    scenario = load_scenario(Path("scenarios/race/qatar-race-l10-map2-rebound.yaml"))
    result = run_what_if(scenario)

    assert result.scenario_id == scenario.scenario_id
    assert result.summary.degradation_delay_laps == 3
