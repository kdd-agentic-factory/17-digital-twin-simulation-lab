"""Explicit workshop inputs; configuration is not a validated force model."""
from typing import Literal, Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_serializer, model_validator

from .measurements import MeasuredValue


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class PointXZ(Strict):
    x: MeasuredValue
    z: MeasuredValue

    @model_validator(mode='after')
    def units(self):
        if self.x.unit != 'm' or self.z.unit != 'm':
            raise ValueError('Point coordinates require metres')
        return self


PointKey = Literal['swingarm_pivot', 'steer_reference', 'front_sprocket', 'cog']


class MechanicalSetup(Strict):
    schema_version: Literal['1.0.0'] = '1.0.0'
    frame: Literal['body_x_forward_z_up'] = 'body_x_forward_z_up'
    points: dict[PointKey, PointXZ] = Field(default_factory=dict, max_length=4)
    rear_radius_m: MeasuredValue | None = None
    swingarm_length_m: MeasuredValue | None = None
    swingarm_angle_rad: MeasuredValue | None = None
    steer_axis_body_rad: MeasuredValue | None = None
    fork_length_m: MeasuredValue | None = None
    fork_compression_m: MeasuredValue | None = None
    chain_pitch_m: MeasuredValue | None = None
    front_teeth: int | None = Field(default=None, ge=5, le=100)
    rear_teeth: int | None = Field(default=None, ge=5, le=200)

    @model_validator(mode='after')
    def units(self):
        for key in type(self).model_fields:
            item = getattr(self, key)
            if isinstance(item, MeasuredValue) and item.unit != ('rad' if key.endswith('_rad') else 'm'):
                raise ValueError(f'{key}: incompatible unit')
        return self


SettingKey = Literal['front_preload_m', 'front_air_gap_m', 'front_spring_rate_n_m',
    'front_compression_clicks', 'front_rebound_clicks', 'rear_preload_m',
    'rear_spring_rate_n_m', 'rear_lsc_clicks', 'rear_hsc_clicks', 'rear_rebound_clicks']
ComponentKey = Literal['fork_cap', 'fork_outer', 'fork_spring', 'fork_cartridge',
    'rear_shock', 'rear_spring', 'rear_linkage', 'swingarm_pivot', 'rear_drive']


class ShimLayer(Strict):
    outer_m: float = Field(gt=0)
    inner_m: float = Field(ge=0)
    thickness_m: float = Field(gt=0)
    count: int = Field(default=1, ge=1, le=100)

    @model_validator(mode='after')
    def diameter(self):
        if self.inner_m >= self.outer_m:
            raise ValueError('Shim inner diameter must be smaller than outer diameter')
        return self


class ComponentConfiguration(Strict):
    settings: dict[SettingKey, float] = Field(default_factory=dict, max_length=10)
    shim_stack: list[ShimLayer] = Field(default_factory=list, max_length=100)
    source: str = Field(default='', max_length=300)
    models: dict[ComponentKey, Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=160)]] = Field(default_factory=dict, max_length=9)

    @model_validator(mode='after')
    def values(self):
        for key, value in self.settings.items():
            if value < 0 or ('clicks' in key and not value.is_integer()):
                raise ValueError('Nonnegative settings and integer clicks required')
            if ('rate' in key or 'gap' in key) and value <= 0:
                raise ValueError('Positive rate and air gap required')
        return self


class SpecificationRef(Strict):
    id: str = Field(pattern=r'^[a-f0-9-]{36}$')
    revision: int = Field(ge=1)
    digest: str = Field(pattern=r'^[a-f0-9]{64}$')


class WorkshopSetupFields(Strict):
    mechanical: MechanicalSetup | None = None
    component_configuration: ComponentConfiguration | None = None
    specification_refs: list[SpecificationRef] | None = Field(default=None, max_length=50)

    @model_serializer(mode='wrap')
    def historical_shape(self, handler):
        data = handler(self)
        for key in ('mechanical', 'component_configuration', 'specification_refs'):
            if data.get(key) is None:
                data.pop(key, None)
        return data


class SpecificationInput(Strict):
    component: ComponentKey
    model_reference: str = Field(min_length=1, max_length=160)
    operation: str = Field(min_length=1, max_length=100)
    source: str = Field(default='', max_length=500)
    page: str = Field(default='', max_length=80)
    tool: str = Field(default='', max_length=160)
    torque_nm: float | None = Field(default=None, gt=0, le=10000)
    setting: SettingKey | Literal['fork_length_m', 'fork_compression_m', 'swingarm_angle_rad', 'steer_axis_body_rad', 'offset_m'] | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = Field(default=None, gt=0)
    unit: Literal['m', 'rad', 'N/m', 'clicks'] | None = None
    zero_reference: str = Field(default='', max_length=200)
    conditions: str = Field(default='', max_length=1500)

    @model_validator(mode='after')
    def bounds(self):
        if (self.minimum is None) != (self.maximum is None):
            raise ValueError('Both range bounds required')
        if self.minimum is not None and self.minimum > self.maximum:
            raise ValueError('Ordered range required')
        if self.setting:
            unit = 'clicks' if self.setting.endswith('clicks') else 'rad' if self.setting.endswith('_rad') else 'N/m' if self.setting.endswith('_n_m') else 'm'
            if self.unit != unit:
                raise ValueError('Setting unit required')
            if self.setting.endswith('clicks') and any(v is not None and (v<0 or not v.is_integer()) for v in (self.minimum,self.maximum,self.step)):
                raise ValueError('Click bounds and step must be nonnegative integers')
        return self
