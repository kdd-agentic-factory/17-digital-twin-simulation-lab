from __future__ import annotations

from typing import Dict, Any
from pydantic import BaseModel, Field

class TireState(BaseModel):
    """Represents the current state of a tire."""
    tire_id: str = Field(..., description="Unique identifier for the tire")
    temperature_c: float = Field(..., description="Current temperature of the tire in Celsius")
    pressure_bar: float = Field(..., description="Current pressure of the tire in bar")
    wear_pct: float = Field(..., description="Current wear percentage (0.0 to 100.0)")
    surface_temp_c: float = Field(..., description="Surface temperature of the tire in Celsius")
    carcass_temp_c: float = Field(..., description="Carcass temperature of the tire in Celsius")
    graining_detected: bool = Field(False, description="Whether graining has been detected")
    blistering_detected: bool = Field(False, description="Whether blistering has been detected")
    additional_metrics: Dict[str, Any] = Field(default_factory=dict, description="Other tire-related metrics")

class TireModel(BaseModel):
    """Represents a tire model specification."""
    tire_model_id: str = Field(..., description="Unique identifier for the tire model")
    name: str = Field(..., description="Name of the tire model")
    manufacturer: str = Field(..., description="Manufacturer of the tire")
    compounds: list[str] = Field(..., description="List of available compounds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional tire model information")
