from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from digital_twin_lab.database import (
    load_dt_what_if_results as load_what_if_results,
    save_what_if_result,
)
from digital_twin_lab.services.what_if_service import WhatIfService

router = APIRouter(tags=["what-if"])
_service = WhatIfService()


class WhatIfRequest(BaseModel):
    scenario_id: str
    circuit_id: str
    session_id: str
    baseline_setup_id: str
    proposed_setup: dict[str, object]
    laps: int = Field(ge=1)
    ambient_temp_c: float
    track_temp_c: float
    tire_compound: str


@router.post("/what-if")
async def run_what_if(request: WhatIfRequest) -> dict[str, object]:
    """Run a what-if simulation and persist the result to the database."""
    result = _service.simulate(
        scenario_id=request.scenario_id,
        circuit_id=request.circuit_id,
        baseline_setup_id=request.baseline_setup_id,
        proposed_setup=request.proposed_setup,
        ambient_temp_c=request.ambient_temp_c,
        track_temp_c=request.track_temp_c,
        laps=request.laps,
    )
    result_dict = result if isinstance(result, dict) else (result.model_dump(mode="json") if hasattr(result, "model_dump") else result)
    try:
        await save_what_if_result(
            scenario_id=request.scenario_id,
            circuit_id=request.circuit_id,
            session_id=request.session_id,
            baseline_setup=request.baseline_setup_id,
            proposed_setup=request.proposed_setup,
            result=result_dict,
        )
    except Exception:
        pass
    return result_dict


@router.get("/what-if")
async def list_what_if_results(scenario_id: str | None = None) -> dict[str, object]:
    """Return persisted what-if results, optionally filtered by scenario."""
    results = await load_what_if_results(scenario_id=scenario_id)
    return {"items": results, "total": len(results)}
