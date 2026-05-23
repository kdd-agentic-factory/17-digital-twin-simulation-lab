from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Corner(BaseModel):
    """Represents a specific corner of a circuit."""
    corner_id: str = Field(..., description="Unique identifier for the corner")
    name: str = Field(..., description="Name of the corner")
    type: str = Field(..., description="Type of corner (e.g., 'high-speed', 'low-speed', 'chicane')")
    length_m: float = Field(..., description="Length of the corner in meters")
    avg_speed_kph: float = Field(..., description="Average speed through the corner in kph")

class CircuitProfile(BaseModel):
    """Represents the profile of a circuit."""
    circuit_id: str = Field(..., description="Unique identifier for the circuit")
    name: str = Field(..., description="Name of the circuit")
    location: str = Field(..., description="Location of the circuit")
    total_length_m: float = Field(..., description="Total length of the circuit in meters")
    num_corners: int = Field(..., description="Number of corners in the circuit")
    corners: List[Corner] = Field(..., description="List of corners in the circuit")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional circuit information")
