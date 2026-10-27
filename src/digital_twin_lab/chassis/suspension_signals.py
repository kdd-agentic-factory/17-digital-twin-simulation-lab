"""Original-clock inspection and movement observations; never hydraulic diagnosis."""
import math
import statistics
from .signal_models import SignalSeries, SignalQuality


def inspect_signal(series: SignalSeries) -> SignalQuality:
    ts, vs = series.times_s, series.values
    reasons=[]
    if len(ts)!=len(vs) or len(ts)<2:
        return SignalQuality('blocked',['insufficient_or_mismatched_samples'],None,None,None,[],len(vs))
    if not all(math.isfinite(v) for v in ts+vs):
        return SignalQuality('blocked',['nonfinite_sample'],None,None,None,[],len(vs))
    steps=[b-a for a,b in zip(ts,ts[1:])]
    if any(d<=0 for d in steps):
        return SignalQuality('blocked',['non_increasing_clock'],None,None,None,[],len(vs))
    dt=statistics.median(steps)
    jitter=max(abs(d-dt)/dt for d in steps)
    intervals=[]
    start=ts[0]
    for i,d in enumerate(steps):
        if d>1.5*dt:
            intervals.append((start,ts[i]));start=ts[i+1]
    intervals.append((start,ts[-1]))
    if len(intervals)>1: reasons.append('clock_gap')
    if jitter>.01+1e-10: reasons.append('clock_jitter_exceeds_policy')
    return SignalQuality('blocked' if reasons else 'eligible',reasons,dt,1/dt,jitter,intervals,len(vs))


def movement_metrics(series: SignalSeries, velocity: SignalSeries | None, bins: int=40) -> dict:
    import numpy as np
    q=inspect_signal(series)
    if any(r in q.reasons for r in ('nonfinite_sample','non_increasing_clock','insufficient_or_mismatched_samples')):
        raise ValueError(','.join(q.reasons))
    if series.unit not in ('m','m/s') or not 2<=bins<=100 or len(series.values)>250000:
        raise ValueError('invalid_movement_input')
    result={'sample_count':len(series.values),'duration_s':series.times_s[-1]-series.times_s[0],
            'force_status':'not_measured','velocity_status':'not_available','warnings':q.reasons}
    if series.unit=='m':result.update(minimum_m=min(series.values),maximum_m=max(series.values),displacement_status='measured')
    else:
        result['displacement_status']='not_available'
        velocity=series
    if velocity is not None:
        if velocity.unit!='m/s' or velocity.times_s!=series.times_s or len(velocity.values)!=len(series.values) or not all(v is None or math.isfinite(v) for v in velocity.values):
            raise ValueError('velocity_clock_or_unit_mismatch')
        valid=[v for v in velocity.values if v is not None]
        counts,edges=np.histogram(valid,bins=bins)
        result.update(velocity_status=velocity.provenance.get('method','measured'),velocity_histogram={'edges_m_s':edges.tolist(),'counts':counts.tolist()},compression_samples=sum(v>0 for v in valid),extension_samples=sum(v<0 for v in valid))
    return result
