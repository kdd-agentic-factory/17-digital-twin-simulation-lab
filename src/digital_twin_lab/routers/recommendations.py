from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from digital_twin_lab.services.recommendation_validation_service import RecommendationValidationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
service = RecommendationValidationService()


class RecommendationPayload(BaseModel):
    target_component: str
    action: str
    value: str
    reasoning: str
    confidence_score: float
    risk_level: str
    expected_impact: str


class RecommendationSimulationInput(BaseModel):
    laps: int
    ambient_temp_c: float
    track_temp_c: float
    tire_compound: str


class RecommendationValidationRequest(BaseModel):
    recommendation_id: str
    scenario_id: str
    circuit_id: str
    baseline_setup_id: str
    recommendation: RecommendationPayload
    simulation_input: RecommendationSimulationInput


@router.post("/validate")
def validate_recommendation(request: RecommendationValidationRequest) -> dict[str, object]:
    return service.validate(
        recommendation_id=request.recommendation_id,
        scenario_id=request.scenario_id,
        recommendation_risk=request.recommendation.risk_level,
        part_id=request.recommendation.value,
        circuit_id=request.circuit_id,
        confidence=request.recommendation.confidence_score,
        ambient_temp_c=request.simulation_input.ambient_temp_c,
        track_temp_c=request.simulation_input.track_temp_c,
    )
