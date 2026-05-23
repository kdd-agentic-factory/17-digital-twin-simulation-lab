from __future__ import annotations

from fastapi import APIRouter

from digital_twin_lab.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
service = ScenarioService()


@router.get("")
def list_scenarios() -> dict[str, object]:
    return {"items": service.list_scenarios(), "message": "Catalog-backed MVP scenarios."}


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, object]:
    return service.get_scenario(scenario_id).model_dump(mode="json")
