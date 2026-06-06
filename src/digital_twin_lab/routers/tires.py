from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from digital_twin_lab.services import pressure_sweep
from digital_twin_lab.services.tire_prediction_service import TirePredictionService

router = APIRouter(prefix="/tires", tags=["tires"])
service = TirePredictionService()


class TireCollapseRequest(BaseModel):
    tire_id: str
    compound: str
    circuit_id: str
    current_wear_pct: float = Field(ge=0.0, le=100.0)
    current_carcass_temp_c: float
    stint_laps: int = Field(ge=1)
    ambient_temp_c: float
    track_temp_c: float
    aggression_index: float = Field(ge=0.0, le=1.0)


@router.post("/predict-collapse")
def predict_collapse(request: TireCollapseRequest) -> dict[str, object]:
    return service.predict_collapse(
        tire_id=request.tire_id,
        compound=request.compound,
        circuit_id=request.circuit_id,
        current_wear_pct=request.current_wear_pct,
        current_carcass_temp_c=request.current_carcass_temp_c,
        stint_laps=request.stint_laps,
        aggression_index=request.aggression_index,
    )


class PressureSweepRequest(BaseModel):
    compound: str
    stint_laps: int = Field(ge=1)
    pressures_bar: list[float] = Field(default_factory=lambda: [1.7, 1.8, 1.9, 1.95, 2.0, 2.1, 2.2])
    start_wear_pct: float = Field(0.0, ge=0.0, le=100.0)


@router.post("/pressure-sweep")
def pressure_sweep_endpoint(request: PressureSweepRequest) -> dict[str, object]:
    """Predict tyre degradation / laps-to-cliff across a sweep of cold pressures."""
    return pressure_sweep.sweep(
        compound=request.compound,
        pressures_bar=request.pressures_bar,
        stint_laps=request.stint_laps,
        start_wear_pct=request.start_wear_pct,
    )
