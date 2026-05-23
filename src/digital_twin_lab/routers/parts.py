from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from digital_twin_lab.services.part_simulation_service import PartSimulationService

router = APIRouter(prefix="/parts", tags=["parts"])
service = PartSimulationService()


class PartSimulationRequest(BaseModel):
    scenario_id: str
    circuit_id: str
    part_id: str
    installation_confidence: float
    ambient_temp_c: float
    track_temp_c: float


@router.post("/simulate")
def simulate_part(request: PartSimulationRequest) -> dict[str, object]:
    return {
        "scenario_id": request.scenario_id,
        **service.simulate_part_candidate(
            part_id=request.part_id,
            circuit_id=request.circuit_id,
            installation_confidence=request.installation_confidence,
            ambient_temp_c=request.ambient_temp_c,
            track_temp_c=request.track_temp_c,
        ),
    }


@router.get("/catalog/{part_id}")
def get_part_catalog_entry(part_id: str) -> dict[str, object]:
    return service.get_part(part_id)
