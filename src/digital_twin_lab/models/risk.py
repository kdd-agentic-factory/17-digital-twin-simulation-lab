from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RiskClassification(BaseModel):
    """Represents the classification of a risk."""
    risk_id: str = Field(..., description="Unique identifier for the risk")
    level: str = Field(..., description="Risk level (e.g., 'low', 'medium', 'high', 'critical')")
    category: str = Field(..., description="Category of the risk (e.g., 'thermal', 'stability', 'spin', 'mechanical')")
    description: str = Field(..., description="Detailed description of the risk")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of the risk occurring")
    impact: float = Field(..., ge=0.0, le=1.0, description="Potential impact of the risk")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Suggested strategies to mitigate the risk")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence for the risk classification")
