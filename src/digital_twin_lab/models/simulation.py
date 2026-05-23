from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .risk import RiskClassification

class SimulationSummary(BaseModel):
    """Represents a summary of the simulation results."""
    spin_t05_delta_pct: float = Field(..., description="Change in spin percentage at 5% load")
    rear_carcass_temp_delta_c: float = Field(..., description="Change in rear carcass temperature in Celsius")
    lap_time_delta_s: float = Field(..., description="Change in lap time in seconds")
    degradation_delay_laps: int = Field(..., description="Estimated delay in degradation in laps")

class SimulationRequest(BaseModel):
    """Represents a request to run a simulation."""
    scenario_id: str = Field(..., description="The ID of the scenario to simulate")
    iterations: int = Field(default=1, ge=1, description="Number of Monte Carlo iterations to run")
    use_real_time_data: bool = Field(default=False, description="Whether to use real-time telemetry data if available")

class SimulationResult(BaseModel):
    """Represents the result of a simulation."""
    scenario_id: str = Field(..., description="The ID of the scenario simulated")
    risk_classification: RiskClassification = Field(..., description="The classified risk of the simulation result")
    summary: SimulationSummary = Field(..., description="Summary of the simulation outcomes")
    recommendation: str = Field(..., description="The resulting technical recommendation")
    evidence: List[str] = Field(..., description="List of evidence points supporting the recommendation and risk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional simulation metadata")
