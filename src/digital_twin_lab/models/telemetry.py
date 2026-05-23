from __future__ import annotations

from pydantic import BaseModel, Field


class TelemetrySnapshot(BaseModel):
    """Minimal telemetry context used by MVP simulations."""

    speed_kph: float = Field(default=0.0)
    rear_carcass_temp_c: float = Field(default=0.0)
    rear_spin_pct: float = Field(default=0.0)
    lean_angle_deg: float = Field(default=0.0)
