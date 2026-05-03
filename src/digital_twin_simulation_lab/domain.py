from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt


SessionName = Literal["pre-gp", "fp1", "fp2", "qualifying", "race"]
RiskLevel = Literal["low", "medium-low", "medium", "high"]


class SetupChanges(BaseModel):
    rear_rebound_clicks: int = 0
    front_rebound_clicks: int = 0
    rear_pressure_delta_bar: float = 0.0
    front_pressure_delta_bar: float = 0.0
    engine_map: str = "baseline"
    aero_package: str = "baseline"
    apply_from_lap: PositiveInt = 1


class BaselineTelemetry(BaseModel):
    rear_carcass_temp_c: float = Field(..., ge=40.0, le=180.0)
    rear_pressure_bar: float = Field(..., ge=1.0, le=3.0)
    spin_t05_pct: float = Field(..., ge=0.0, le=100.0)


class SimulationScenario(BaseModel):
    scenario_id: str = Field(..., min_length=3)
    circuit: str = Field(..., min_length=2)
    session: SessionName
    base_lap_time_s: PositiveFloat
    laps: PositiveInt
    changes: SetupChanges
    baseline: BaselineTelemetry


class SimulationSummary(BaseModel):
    spin_t05_delta_pct: float
    rear_carcass_temp_delta_c: float
    lap_time_delta_s: float
    degradation_delay_laps: int


class SimulationResult(BaseModel):
    scenario_id: str
    risk: RiskLevel
    recommendation: str
    summary: SimulationSummary
    evidence: list[str]
