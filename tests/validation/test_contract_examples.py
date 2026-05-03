import yaml


def test_scenario_contract_has_required_fields():
    with open("data-contracts/simulation-scenario.schema.yaml", encoding="utf-8") as file:
        schema = yaml.safe_load(file)

    required = set(schema["required"])

    assert {"scenario_id", "circuit", "session", "base_lap_time_s", "laps", "changes", "baseline"} <= required
