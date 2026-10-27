"""Top straight chain tangent and line intersection, without squat certification."""
import math


def upper_tangent(a,b,ra,rb):
    if not all(math.isfinite(v) for v in (*a,*b,ra,rb)) or min(ra,rb)<=0:
        raise ValueError('invalid_sprocket_domain')
    dx,dz=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dz)
    if length<=abs(ra-rb)+1e-9:
        raise ValueError('chain_tangent_infeasible')
    ux,uz=dx/length,dz/length
    c=(ra-rb)/length;s=math.sqrt(1-c*c)
    normals=[(c*ux-sign*s*uz,c*uz+sign*s*ux) for sign in (1,-1)]
    nx,nz=max(normals,key=lambda n:n[1])
    return ([a[0]+ra*nx,a[1]+ra*nz],[b[0]+rb*nx,b[1]+rb*nz])


def line_intersection(a,b,c,d):
    u=(b[0]-a[0],b[1]-a[1]);v=(d[0]-c[0],d[1]-c[1])
    cross=u[0]*v[1]-u[1]*v[0]
    norm=math.hypot(*u)*math.hypot(*v)
    if norm==0 or abs(cross)<=1e-9*norm:
        return None
    w=(c[0]-a[0],c[1]-a[1]);t=(w[0]*v[1]-w[1]*v[0])/cross
    point=[a[0]+t*u[0],a[1]+t*u[1]]
    return point if all(math.isfinite(x) and abs(x)<=10000 for x in point) else None


def evaluate_chain(points, mechanical):
    result=dict(model_version='chain-tangent-1.0.0',metrics={},segments={},points={},missing=[],warnings=[],
        anti_squat_status='unavailable',anti_squat_reason='independent_reference_missing')
    for key in ('rear_axle','swingarm_pivot','front_sprocket'):
        if key not in points:
            result['missing'].append(key)
    if mechanical is None or mechanical.chain_pitch_m is None or mechanical.chain_pitch_m.value is None:
        result['missing'].append('chain_pitch_m')
    for key in ('front_teeth','rear_teeth'):
        if mechanical is None or getattr(mechanical,key) is None:
            result['missing'].append(key)
    if result['missing']:
        return result
    pitch=mechanical.chain_pitch_m.value
    if mechanical.chain_pitch_m.provenance=='assumed':
        result['warnings'].append('assumed:chain_pitch_m')
    if not 0<pitch<.1:
        result['warnings'].append('invalid_chain_pitch')
        return result
    ra=pitch/(2*math.sin(math.pi/mechanical.rear_teeth))
    rb=pitch/(2*math.sin(math.pi/mechanical.front_teeth))
    try:
        a,b=upper_tangent(points['rear_axle'],points['front_sprocket'],ra,rb)
        result['segments']['chain_pull']=[a,b]
        ifc=line_intersection(a,b,points['rear_axle'],points['swingarm_pivot'])
        if ifc is None:
            result['warnings'].append('parallel_or_remote_ifc')
        else:
            result['points']['ifc']=ifc
            result['segments']['ifc_line']=[[0,0],ifc]
    except ValueError as exc:
        result['warnings'].append(str(exc))
    return result
