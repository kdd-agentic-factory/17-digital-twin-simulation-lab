"""Stationary ideal aggregate model. Not Pacejka, tire identification or fall detection."""
import math

from pydantic import Field
from .workshop_models import Strict


class CorneringInput(Strict):
    speed_m_s: float = Field(ge=0)
    radius_m: float = Field(gt=0)
    mass_kg: float = Field(gt=0)
    longitudinal_force_n: float | None = None
    normal_force_n: float | None = Field(default=None,gt=0)
    mu_x: float | None = Field(default=None,gt=0)
    mu_y: float | None = Field(default=None,gt=0)
    derive_normal_load: bool = False
    input_source: str = Field(default='',max_length=500)
    aero_hypothesis_n: float | None = Field(default=None,ge=0)
    rider_hanging_pct: float | None = Field(default=None,ge=0,le=100)


def evaluate_cornering(input: CorneringInput):
    result=dict(schema_version='1.0.0',model_version='cornering-ideal-1.0.0',status='available',metrics={},warnings=[],
        assumptions=['steady_state','level_ground','aggregate_bike_and_rider','no_aerodynamics','no_posture_correction','not_a_grip_measurement','uncertainty_not_propagated'],
        envelope=dict(status='missing_inputs',label='idealized_friction_ellipse',missing=[]))
    if input.aero_hypothesis_n is not None or input.rider_hanging_pct is not None:
        result['warnings'].append('aero_and_posture_not_modelled')
    try:
        ay=input.speed_m_s**2/input.radius_m;fy=input.mass_kg*ay
        metrics=dict(lateral_acceleration_m_s2=ay,lateral_force_n=fy,combined_lean_rad=math.atan2(ay,9.80665))
        if not all(math.isfinite(v) for v in metrics.values()):
            raise ValueError('cornering_overflow')
        result['metrics']=metrics
        fz=input.normal_force_n
        if fz is None and input.derive_normal_load:
            fz=input.mass_kg*9.80665
            result['warnings'].append('normal_load_is_idealized_mass_times_gravity')
        candidates=dict(longitudinal_force_n=input.longitudinal_force_n,normal_force_n=fz,mu_x=input.mu_x,mu_y=input.mu_y)
        result['envelope']['missing']=[k for k,v in candidates.items() if v is None]
        if not result['envelope']['missing']:
            cap_x=input.mu_x*fz;cap_y=input.mu_y*fz
            ratio=math.hypot(input.longitudinal_force_n/cap_x,fy/cap_y)
            if not all(math.isfinite(v) and v>0 for v in (cap_x,cap_y)) or not math.isfinite(ratio):
                raise ValueError('envelope_overflow')
            result['envelope'].update(status='available',demand_ratio=ratio,capacity_x_n=cap_x,capacity_y_n=cap_y,
                demand_fx_n=input.longitudinal_force_n,demand_fy_n=fy,normal_force_n=fz)
            if ratio>1:
                result['warnings'].append('demand_exceeds_assumed_envelope')
    except (ValueError,OverflowError,ZeroDivisionError):
        result.update(status='out_of_domain',metrics={},warnings=['cornering_or_envelope_overflow'],envelope={'status':'unavailable','label':'idealized_friction_ellipse','missing':[]})
    return result
