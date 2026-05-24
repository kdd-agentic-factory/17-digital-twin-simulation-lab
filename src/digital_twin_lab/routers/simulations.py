from __future__ import annotations

from fastapi import APIRouter

from digital_twin_lab.database import load_recent_simulations, save_simulation_result
from digital_twin_lab.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulations", tags=["simulations"])
_service = SimulationService()


@router.get("")
async def list_simulations() -> dict[str, object]:
    """Return recent simulation results from the database (falls back to in-memory)."""
    try:
        results = await load_recent_simulations(limit=50)
    except Exception:
        results = []

    if not results:
        # Seed with a default simulation on first access
        from digital_twin_lab.models.simulation import SimulationRequest
        from digital_twin_lab.services.scenario_service import ScenarioService
        scenario = ScenarioService().get_scenario("jerez-map2-rebound")
        result = _service.run(SimulationRequest(scenario_id=scenario.scenario_id), scenario)
        result_dict = result.model_dump(mode="json")
        try:
            await save_simulation_result(scenario_id=result.scenario_id, result=result_dict)
        except Exception:
            pass
        results = [result_dict]
    return {"items": results, "total": len(results)}
