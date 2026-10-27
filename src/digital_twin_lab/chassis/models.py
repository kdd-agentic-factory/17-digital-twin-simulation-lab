from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from .measurements import MeasuredValue
from .workshop_models import WorkshopSetupFields

MODEL_VERSION = 'chassis-planar-1.1.0'


class LinkagePoint(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    wheel_m: float = Field(ge=0, le=2)
    shock_m: float = Field(ge=0, le=1)


class LinkageCurve(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    points: list[LinkagePoint] = Field(min_length=3, max_length=500)
    provenance: Literal['measured', 'assumed']
    reference: Literal['full_extension']
    source: str = Field(min_length=3, max_length=300)

    @model_validator(mode='after')
    def check_curve(self):
        if self.points[0].wheel_m != 0 or self.points[0].shock_m != 0:
            raise ValueError('Curve must start at full extension: wheel=0, shock=0')
        if any(b.wheel_m <= a.wheel_m or b.shock_m <= a.shock_m for a,b in zip(self.points, self.points[1:])):
            raise ValueError('Wheel and shock coordinates must be strictly increasing')
        return self


class SetupRevision(WorkshopSetupFields):
    model_config = ConfigDict(extra='forbid')
    id: str
    bike_id: str = Field(min_length=1, max_length=120)
    version: int = Field(ge=1)
    values: dict[str, MeasuredValue]
    linkage_curve: LinkageCurve | None = None


class PhysicsResult(BaseModel):
    model_version: str = MODEL_VERSION
    metrics: dict[str, float] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
