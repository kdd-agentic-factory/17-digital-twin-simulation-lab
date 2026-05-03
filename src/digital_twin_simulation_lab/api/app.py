from fastapi import FastAPI

from digital_twin_simulation_lab import __version__
from digital_twin_simulation_lab.domain import SimulationResult, SimulationScenario
from digital_twin_simulation_lab.simulators import run_what_if

app = FastAPI(
    title="Digital Twin Simulation Lab",
    version=__version__,
    description="What-if simulation API for race setup, tire, engine map and strategy hypotheses.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "digital-twin-simulation-lab"}


@app.post("/v1/simulations/what-if", response_model=SimulationResult)
def simulate_what_if(scenario: SimulationScenario) -> SimulationResult:
    return run_what_if(scenario)
