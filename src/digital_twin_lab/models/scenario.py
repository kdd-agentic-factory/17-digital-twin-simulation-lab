from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from .setup import SetupChange
from .part import PartCandidate

class SimulationScenario(BaseModel):
    """Represents a simulation scenario for testing setup or part changes."""
    scenario_id: str = Field(..., description="Unique identifier for the scenario")
    name: str = Field(..., description="Human-readable name of the scenario")
    scenario_type: str = Field(..., description="Type of scenario (e.g., 'baseline', 'setup_change', 'part_change')")
    circuit_id: str = Field(..., description="ID of the circuit being used")
    session_id: str = Field(..., description="ID of the session (e.g., 'race', 'fp1')")
    baseline_setup_id: str = Field(..., description="ID of the baseline setup to compare against")
    setup_change: Optional[SetupChange] = Field(None, description="The setup change to be applied")
    part_candidate: Optional[PartCandidate] = Field(None, description="The candidate part to be tested")
    tire_model_id: Optional[str] = Field(None, description="ID of the tire model to use")
    lap_range: Tuple[int, int] = Field(..., description="The range of laps to simulate (start_lap, end_lap)")
    corner_ids: List[str] = Field(default_factory=list, description="Specific corners to focus on in the simulation")
    assumptions: List[str] = Field(default_factory=list, description="List of assumptions made for this scenario")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional scenario metadata")
