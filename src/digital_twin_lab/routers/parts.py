from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

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


class FEARequest(BaseModel):
    material: str = Field(..., description="steel_4340|alu_7075_t6|ti_6al4v|magnesium_az80|cfrp_t700")
    section: dict[str, object] = Field(..., description="{'type':'tube','od':25,'id':20} (mm)")
    loads: dict[str, float] = Field(..., description="{'bending_moment_Nm':…, 'torque_Nm':…, 'axial_N':…}")
    operating_temp_c: float = 20.0
    target_safety_factor: float = Field(1.5, gt=0)


@router.post("/fea")
def run_part_fea(request: FEARequest) -> dict[str, object]:
    """FEM/FEA structural check — bending/torsion/thermal von-Mises + safety factor (§8.3)."""
    return service.run_fea(
        material=request.material,
        section=request.section,
        loads=request.loads,
        operating_temp_c=request.operating_temp_c,
        target_safety_factor=request.target_safety_factor,
    )
