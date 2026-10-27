"""Rigid planar pose on level ground, no equilibrium inferred from acceleration."""
import math

from pydantic import Field

from .measurements import MeasuredValue
from .workshop_models import Strict, WorkshopSetupFields

POSE_VERSION = 'chassis-workshop-planar-1.1.0'


class PoseInput(WorkshopSetupFields):
    values: dict[str, MeasuredValue] = Field(default_factory=dict, max_length=30)


class PoseResult(Strict):
    model_version: str = POSE_VERSION
    status: str = 'missing_inputs'
    points: dict[str, list[float]] = Field(default_factory=dict)
    segments: dict[str, list[list[float]]] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=lambda:['upright_zero_steer','level_ground','rigid_chassis','prescribed_suspension_position','not_dynamic_equilibrium'])


def evaluate_pose(input: PoseInput, *, check_reference: bool = True) -> PoseResult:
    result=PoseResult()
    mech=input.mechanical
    def read(key, item, unit):
        if item is None or item.value is None:
            result.missing.append(key)
            return None
        if item.unit != unit:
            result.warnings.append('invalid_unit:'+key)
            return None
        if item.provenance == 'assumed':
            result.warnings.append('assumed:'+key)
        return item.value
    values={k:read(k,input.values.get(k),u) for k,u in [('front_radius_m','m'),('rake_rad','rad'),('offset_m','m')]}
    for k,u in [('rear_radius_m','m'),('swingarm_length_m','m'),('swingarm_angle_rad','rad'),('steer_axis_body_rad','rad'),('fork_length_m','m')]:
        values[k]=read(k,getattr(mech,k,None),u)
    points={}
    for k in ('swingarm_pivot','steer_reference'):
        point=mech.points.get(k) if mech else None
        points[k]=[read(k+'.'+axis,getattr(point,axis,None),'m') for axis in ('x','z')]
    if result.missing or result.warnings and any(w.startswith('invalid_unit:') for w in result.warnings):
        return result
    try:
        r,rr,a,d,l,alpha,f=(values[k] for k in ('front_radius_m','rear_radius_m','steer_axis_body_rad','offset_m','swingarm_length_m','swingarm_angle_rad','fork_length_m'))
        compression=0
        if mech.fork_compression_m is not None:
            compression=read('fork_compression_m',mech.fork_compression_m,'m')
            if compression is None:
                return result
        if not(0<r<=1 and 0<rr<=1 and 0<=a<math.pi/3 and 0<=d<r and 0<l<=3 and 0<f<=3 and 0<=compression<f and abs(alpha)<math.pi/2):
            raise ValueError('invalid_pose_domain')
        if any(abs(v)>10 for p in points.values() for v in p):
            raise ValueError('invalid_coordinate_domain')
        p,h=points['swingarm_pivot'],points['steer_reference']
        rear=[p[0]-l*math.cos(alpha),p[1]-l*math.sin(alpha)]
        front=[h[0]+(f-compression)*math.sin(a)+d*math.cos(a),h[1]-(f-compression)*math.cos(a)+d*math.sin(a)]
        dx,dz=front[0]-rear[0],front[1]-rear[1]
        length=math.hypot(dx,dz)
        if dx<=0 or length<=abs(r-rr):
            raise ValueError('ground_constraints_infeasible')
        pitch=math.asin((r-rr)/length)-math.atan2(dz,dx)
        rake=a+pitch
        if abs(pitch)>=math.pi/3 or not 0<=rake<math.pi/3:
            raise ValueError('pose_rake_outside_planar_domain')
        cs,sn=math.cos(pitch),math.sin(pitch)
        def world(point):
            x,z=point[0]-rear[0],point[1]-rear[1]
            return [x*cs-z*sn,rr+x*sn+z*cs]
        result.points={'rear_axle':world(rear),'front_axle':world(front),'rear_contact':[0,0]}
        for key,point in mech.points.items():
            if point.x.value is None or point.z.value is None:
                continue
            for axis in ('x','z'):
                read(key+'.'+axis,getattr(point,axis),'m')
            if max(abs(point.x.value),abs(point.z.value))>10:
                raise ValueError('invalid_coordinate_domain')
            result.points[key]=world([point.x.value,point.z.value])
        wheelbase=result.points['front_axle'][0]
        trail=(r*math.sin(rake)-d)/math.cos(rake)
        result.points['front_contact']=[wheelbase,0]
        result.points['steer_ground']=[wheelbase+trail,0]
        # The steering axis is offset from the axle perpendicular to its direction.
        axis=[wheelbase-d*math.cos(rake),r-d*math.sin(rake)]
        result.segments={'steer_axis':[[wheelbase+trail,0],[axis[0]-.5*math.sin(rake),axis[1]+.5*math.cos(rake)]],
            'swingarm':[result.points['rear_axle'],result.points['swingarm_pivot']],
            'fork':[result.points['front_axle'],result.points['steer_reference']]}
        result.metrics=dict(rake_rad=rake,trail_m=trail,normal_trail_m=trail*math.cos(rake),wheelbase_m=wheelbase,
            front_radius_m=r,rear_radius_m=rr,body_pitch_rad=pitch,ground_residual_m=abs(result.points['front_axle'][1]-r))
        if not all(math.isfinite(v) for v in result.metrics.values()):
            raise ValueError('pose_overflow')
        if check_reference:
            # Fixed numerical contract, not a claim about measurement accuracy.
            # Uncertainty does not silently widen consistency tolerances.
            inconsistent=[]
            if abs(rake-values['rake_rad'])>1e-6:
                inconsistent.append('world_rake_inconsistent_with_pose')
            declared=input.values.get('wheelbase_m')
            if declared and declared.value is not None and (declared.unit!='m' or abs(wheelbase-declared.value)>1e-6):
                inconsistent.append('wheelbase_inconsistent_with_pose')
            if inconsistent:
                result.status='inconsistent_inputs';result.warnings.extend(inconsistent)
                result.points={};result.segments={};result.metrics={}
                return result
        result.status='available'
    except (ValueError,OverflowError,ZeroDivisionError) as exc:
        result.status='out_of_domain'
        result.points={};result.segments={};result.metrics={}
        result.warnings.append(str(exc))
    return result
