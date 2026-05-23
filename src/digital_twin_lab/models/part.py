from __future__ import annotations

from typing import Optional, Any
from pydantic import BaseModel, Field

class Part(BaseModel):
    """Represents a vehicle part or component."""
    part_id: str = Field(..., description="Unique identifier for the part")
    name: str = Field(..., description="Human-readable name of the part")
    category: str = Field(..., description="Category of the part (e.g., 'aerodynamic', 'suspension', 'cooling')")
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the part")
    specifications: dict[str, Any] = Field(default_factory=dict, description="Technical specifications of the part")

class PartCandidate(BaseModel):
    """Represents a candidate part for a simulation scenario."""
    part: Part
    impact_type: str = Field(..., description="Type of impact this part is expected to have (e.g., 'drag_reduction', 'downforce_increase')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of the predicted impact")
