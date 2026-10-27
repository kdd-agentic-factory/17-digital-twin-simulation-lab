from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MeasuredValue(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    value: float | None = None
    unit: str
    provenance: Literal['measured', 'assumed']
    uncertainty: float | None = Field(default=None, ge=0)
