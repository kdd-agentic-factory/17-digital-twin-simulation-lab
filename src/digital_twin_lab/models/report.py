from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SimulationReport(BaseModel):
    """Represents a comprehensive simulation report."""
    report_id: str = Field(..., description="Unique identifier for the report")
    scenario_id: str = Field(..., description="The scenario that was simulated")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the report was generated")
    summary: Dict[str, Any] = Field(..., description="Executive summary of the simulation results")
    key_findings: List[str] = Field(..., description="List of key findings from the simulation")
    risks: List[Dict[str, Any]] = Field(..., description="List of identified risks")
    recommendations: List[Dict[str, Any]] = Field(..., description="List of recommended actions")
    visualizations: List[str] = Field(default_factory=list, description="Links to generated visualizations/plots")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional report metadata")
