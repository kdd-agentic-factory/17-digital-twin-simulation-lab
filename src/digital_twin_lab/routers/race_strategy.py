"""Race strategy simulation endpoint."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from digital_twin_lab.models.race_strategy import RaceStrategyRequest, RaceStrategyResult
from digital_twin_lab.services.race_strategy_service import RaceStrategyService

router = APIRouter(prefix="/simulations/race-strategy", tags=["race-strategy"])
_service = RaceStrategyService()


@router.post("", response_model=RaceStrategyResult, status_code=201)
async def create_race_strategy(request: RaceStrategyRequest) -> RaceStrategyResult:
    """Compute the optimal tyre strategy for a MotoGP race using the Pacejka tire model.

    Evaluates all 1-stop (and optionally 2-stop) strategies over a pit-lap window
    and returns the minimum total race time with per-lap telemetry.
    """
    result = await asyncio.to_thread(_service.simulate, request)

    try:
        from digital_twin_lab.database import save_race_strategy
        asyncio.ensure_future(save_race_strategy(result.strategy_id, result.circuit_id, result.model_dump(mode="json")))
    except Exception:
        pass

    return result


@router.get("", response_model=list[dict])
async def list_race_strategies(
    circuit_id: str | None = Query(default=None, description="Filter by circuit"),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    """Return previously computed race strategies from the database."""
    from digital_twin_lab.database import load_race_strategies
    return await load_race_strategies(circuit_id=circuit_id, limit=limit)
