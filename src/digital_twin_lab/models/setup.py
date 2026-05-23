from __future__ import annotations

from typing import Optional, Any
from pydantic import BaseModel, Field

class SetupChange(BaseModel):
    """Represents a change in vehicle setup."""
    parameter_name: str = Field(..., description="Name of the setup parameter being changed (e.g., 'rear_rebound')")
    old_value: Any = Field(..., description="The original value of the parameter")
    new_value: Any = Field(..., description="The new value of the parameter")
    unit: Optional[str] = Field(None, description="Unit of measurement for the parameter")
    description: Optional[str] = Field(None, description="Description of why this change is being made")

class SetupComparison(BaseModel):
    """Represents a comparison between two setups."""
    baseline_setup_id: str
    proposed_setup_id: str
    differences: list[SetupChange]
