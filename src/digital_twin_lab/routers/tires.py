from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from digital_twin_lab.services import pressure_sweep
from digital_twin_lab.services.tire_prediction_service import TirePredictionService
from digital_twin_lab.tire import pinn_magic_formula

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


class PINNSample(BaseModel):
    slip_ratio: float
    normal_load_n: float
    temp_c: float
    force_n: float


class PINNRequest(BaseModel):
    samples: list[PINNSample] = Field(..., min_length=8)
    query_load_n: float = 850.0
    query_temp_c: float = 100.0
    epochs: int = Field(300, ge=10, le=2000)


@router.post("/pinn-magic-formula")
def pinn_magic_formula_endpoint(request: PINNRequest) -> dict[str, object]:
    """Estimate Pacejka Magic-Formula coefficients via a Physics-Informed NN (§14.2)."""
    if not pinn_magic_formula.torch_available():
        raise HTTPException(status_code=503, detail="PINN unavailable: torch not installed in this image")
    return pinn_magic_formula.fit_and_predict(
        [s.model_dump() for s in request.samples],
        {"normal_load_n": request.query_load_n, "temp_c": request.query_temp_c},
        epochs=request.epochs,
    )
