"""Finite deterministic search over documented actuator positions."""
from decimal import Decimal, ROUND_FLOOR
from itertools import product
from typing import Literal

from pydantic import Field, model_validator

from .planar_pose import PoseInput, evaluate_pose
from .workshop_models import Strict

ActuatorKey=Literal['fork_length_m','fork_compression_m','swingarm_angle_rad','steer_axis_body_rad','offset_m']


class Actuator(Strict):
    key: ActuatorKey
    minimum: float
    maximum: float
    step: float = Field(gt=0)

    @model_validator(mode='after')
    def ordered(self):
        if self.minimum>self.maximum:
            raise ValueError('Ordered actuator range required')
        return self


class TargetLockInput(Strict):
    base: PoseInput
    target_rake_rad: float
    target_trail_m: float
    rake_tolerance_rad: float = Field(gt=0,le=.1)
    trail_tolerance_m: float = Field(gt=0,le=.05)
    actuators: list[Actuator] = Field(max_length=5)

    @model_validator(mode='after')
    def unique(self):
        if len({a.key for a in self.actuators})!=len(self.actuators):
            raise ValueError('Duplicate actuator')
        return self


def solve_target_lock(input: TargetLockInput):
    result=dict(schema_version='1.0.0',solver_version='target-lock-finite-1.0.0',status='infeasible',reason=None,
        changes={},residuals={},active_limits=[],evaluations=0,missing=[],assumptions=['discrete_documented_actuators','no_dynamic_equilibrium'])
    # This is a proposed alternative, not a claim that its legacy scalars have
    # already been updated. The immutable reference is checked by the API.
    original=evaluate_pose(input.base,check_reference=False)
    if original.status!='available':
        result.update(status='missing_inputs' if original.missing else 'out_of_domain',missing=original.missing,reason='complete_planar_pose_required')
        return result
    def residuals(metrics):
        return {'rake_rad':abs(metrics['rake_rad']-input.target_rake_rad),'trail_m':abs(metrics['trail_m']-input.target_trail_m)}
    def fits(r):
        return r['rake_rad']<=input.rake_tolerance_rad and r['trail_m']<=input.trail_tolerance_m
    # No-op is still required to respect the admissible bounds and actuator grid.
    grids=[];starts=[];count=1
    for actuator in input.actuators:
        obj=input.base.values.get(actuator.key) if actuator.key=='offset_m' else getattr(input.base.mechanical,actuator.key,None)
        if obj is None or obj.value is None:
            result.update(status='missing_inputs',missing=[actuator.key]);return result
        starts.append(obj.value)
        low,high,step=map(lambda x:Decimal(str(x)),(actuator.minimum,actuator.maximum,actuator.step))
        n=int(((high-low)/step).to_integral_value(rounding=ROUND_FLOOR))+1
        count*=n
        if count>5000:
            result.update(status='out_of_domain',reason='search_space_limit');return result
        grids.append([float(low+j*step) for j in range(n)])
    result['residuals']=residuals(original.metrics)
    if not input.actuators:
        result.update(status='feasible' if fits(result['residuals']) else 'infeasible',evaluations=1)
        return result
    best=None
    for values in product(*grids):
        candidate=input.base.model_copy(deep=True)
        for actuator,value in zip(input.actuators,values):
            obj=candidate.values[actuator.key] if actuator.key=='offset_m' else getattr(candidate.mechanical,actuator.key)
            obj.value=value;obj.provenance='assumed'
        pose=evaluate_pose(candidate,check_reference=False);result['evaluations']+=1
        if pose.status!='available':
            continue
        r=residuals(pose.metrics)
        if not fits(r):
            continue
        cost=sum(abs(v-start)/(a.maximum-a.minimum) if a.maximum>a.minimum else 0 for a,v,start in zip(input.actuators,values,starts))
        score=(cost,*values)
        if best is None or score<best[0]:
            best=(score,values,r,pose.metrics)
    if best:
        _,values,r,metrics=best
        result.update(status='feasible',residuals=r,candidate_metrics=metrics,changes={a.key:v for a,v,start in zip(input.actuators,values,starts) if v!=start},
            active_limits=[a.key for a,v in zip(input.actuators,values) if v==a.minimum or v==a.maximum])
    return result
