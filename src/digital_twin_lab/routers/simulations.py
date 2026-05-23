from __future__ import annotations

from fastapi import APIRouter

from digital_twin_lab.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulations", tags=["simulations"])
service = SimulationService()


@router.get("")
def list_simulations() -> dict[str, object]:
    return {"items": service.list_simulations(), "message": "Recent and seeded MVP simulations."}
