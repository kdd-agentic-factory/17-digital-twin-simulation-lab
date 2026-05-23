from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

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
