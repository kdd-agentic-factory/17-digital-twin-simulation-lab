from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from digital_twin_simulation_lab.domain import SimulationScenario
from digital_twin_simulation_lab.simulators import run_what_if


def load_scenario(path: Path) -> SimulationScenario:
    with path.open(encoding="utf-8") as file:
        payload = yaml.safe_load(file)
    return SimulationScenario.model_validate(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a digital twin simulation scenario.")
    parser.add_argument("scenario", type=Path, help="Path to a scenario YAML file.")
    args = parser.parse_args()

    result = run_what_if(load_scenario(args.scenario))
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
