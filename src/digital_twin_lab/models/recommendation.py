from __future__ import annotations

from typing import List, Any, Optional
from pydantic import BaseModel, Field

class Recommendation(BaseModel):
    """Represents a technical recommendation."""
    recommendation_id: str = Field(..., description="Unique identifier for the recommendation")
    target_component: str = Field(..., description="The component the recommendation applies to (e.g., 'rear_suspension', 'engine_map')")
    action: str = Field(..., description="The recommended action (e.g., 'increase_rebound', 'reduce_pressure')")
    value: Any = Field(..., description="The suggested value for the action")
    reasoning: str = Field(..., description="The technical reasoning behind the recommendation")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the recommendation")
    risk_level: str = Field(..., description="Associated risk level (e.g., 'low', 'medium', 'high')")
    expected_impact: str = Field(..., description="Expected impact of the recommendation (e.g., 'lap_time_reduction_0.1s')")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence for the recommendation")
