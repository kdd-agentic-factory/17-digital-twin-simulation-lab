from __future__ import annotations

import argparse
import time
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
    parser.add_argument("scenario", nargs="?", type=Path, help="Path to a scenario YAML file.")
    parser.add_argument("--watch-dir", type=Path, help="Keep running and execute new scenario YAML files from this directory.")
    parser.add_argument("--interval-s", type=float, default=30.0, help="Polling interval for watch mode.")
    args = parser.parse_args()

    if args.watch_dir:
        _watch_scenarios(args.watch_dir, args.interval_s)
        return

    if not args.scenario:
        parser.error("scenario is required unless --watch-dir is provided")

    result = run_what_if(load_scenario(args.scenario))
    print(result.model_dump_json(indent=2))


def _watch_scenarios(watch_dir: Path, interval_s: float) -> None:
    seen: set[Path] = set()
    watch_dir.mkdir(parents=True, exist_ok=True)
    while True:
        for path in sorted(watch_dir.rglob("*.yaml")):
            if path in seen:
                continue
            result = run_what_if(load_scenario(path))
            print(result.model_dump_json(indent=2), flush=True)
            seen.add(path)
        time.sleep(interval_s)


if __name__ == "__main__":
    main()
