"""Pydantic models for race strategy simulation."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


CompoundType = Literal["soft", "medium", "hard"]


class StintSpec(BaseModel):
    compound: CompoundType
    laps: int = Field(ge=1, le=60)


class RaceStrategyRequest(BaseModel):
    circuit_id: str
    race_laps: int = Field(ge=5, le=60, default=25)
    ambient_temp_c: float = Field(ge=5.0, le=55.0, default=30.0)
    track_temp_c: float = Field(ge=10.0, le=65.0, default=40.0)
    compounds: list[CompoundType] = Field(
        default=["medium", "soft"],
        min_length=1,
        max_length=4,
        description="Tyre compounds in stint order (pit strategy sequence).",
    )
    pit_stop_penalty_s: float = Field(ge=15.0, le=35.0, default=22.0)
    setup_stability_score: float = Field(ge=0.0, le=1.0, default=0.75)


class LapData(BaseModel):
    lap: int
    stint: int
    compound: CompoundType
    wear_pct: float
    carcass_temp_c: float
    grip_factor: float
    lap_time_s: float
    cumulative_time_s: float


class StintSummary(BaseModel):
    stint: int
    compound: CompoundType
    start_lap: int
    end_lap: int
    stint_laps: int
    cliff_lap: int
    final_wear_pct: float
    avg_lap_time_s: float


class StrategyVariant(BaseModel):
    pit_laps: list[int]
    total_race_time_s: float
    rank: int


class RaceStrategyResult(BaseModel):
    strategy_id: str
    circuit_id: str
    race_laps: int
    total_race_time_s: float
    pit_stops: int
    pit_stop_penalty_s: float
    compounds_used: list[CompoundType]
    optimal_pit_laps: list[int]
    stints: list[StintSummary]
    lap_by_lap: list[LapData]
    alternatives_evaluated: list[StrategyVariant]
    recommendation: str
    limitations: list[str]
