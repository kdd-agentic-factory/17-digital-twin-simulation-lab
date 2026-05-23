from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from digital_twin_lab.services.what_if_service import WhatIfService

router = APIRouter(tags=["what-if"])
service = WhatIfService()


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
def run_what_if(request: WhatIfRequest) -> dict[str, object]:
    return service.simulate(
        scenario_id=request.scenario_id,
        circuit_id=request.circuit_id,
        baseline_setup_id=request.baseline_setup_id,
        proposed_setup=request.proposed_setup,
        ambient_temp_c=request.ambient_temp_c,
        track_temp_c=request.track_temp_c,
        laps=request.laps,
    )
