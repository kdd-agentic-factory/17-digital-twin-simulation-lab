"""Measured total-force loops. No shim identification or fault classifier."""
import numpy as np
from .signal_models import SignalSeries, BenchConditions
from .suspension_signals import inspect_signal


def bench_curves(force:SignalSeries, displacement:SignalSeries|None, velocity:SignalSeries|None, metadata:BenchConditions)->dict:
    q=inspect_signal(force)
    if q.status!='eligible' or force.unit!='N' or len(force.values)>250000:
        raise ValueError('invalid_force_signal_or_clock')
    if displacement is None and velocity is None:raise ValueError('movement_required')
    for s,u in [(displacement,'m'),(velocity,'m/s')]:
        if s is not None and (s.unit!=u or s.times_s!=force.times_s or len(s.values)!=len(force.values) or not all(v is None and u=='m/s' or v is not None and np.isfinite(v) for v in s.values)):
            raise ValueError('unsynchronized_or_incompatible_bench_signal')
    f=np.asarray(force.values)
    result={'force_definition':metadata.force_definition,'correction_method':metadata.correction_method,
            'temperature_c':metadata.temperature_c,'mounting':metadata.mounting,'cycle_work_j':[],
            'warnings':['measured_force_is_not_isolated_hydraulic_force'] if metadata.force_definition=='total_measured' else ['force_correction_supplied_not_independently_verified'],
            'force_n':force.values,'times_s':force.times_s}
    if displacement is not None:result['displacement_m']=displacement.values
    if velocity is not None:
        result['velocity_m_s']=velocity.values
        result['branch']=['not_available' if v is None else 'compression' if v>0 else 'extension' if v<0 else 'stationary' for v in velocity.values]
    if displacement is not None and metadata.work_convention=='force_along_positive_displacement' and metadata.synchronization_reference:
        x=np.asarray(displacement.values)
        # Mid-stroke same-direction crossings close observed cycles; interpolate only
        # the crossing boundary within adjacent measured samples, never a data gap.
        ref=(float(x.min())+float(x.max()))/2
        crossings=[]
        for i in range(len(x)-1):
            if x[i]<=ref<x[i+1]:
                a=float((ref-x[i])/(x[i+1]-x[i]));crossings.append((i,float(f[i]+a*(f[i+1]-f[i]))))
        for (a,fa),(b,fb) in zip(crossings,crossings[1:]):
            if b-a<4 or not np.any(x[a+1:b+1]<ref):continue
            differences=np.abs(np.diff(x[a:b+2]))
            quiet=differences<=max(float(np.max(differences))*.01,1e-15)
            longest=current=0
            for stopped in quiet:
                current=current+1 if stopped else 0
                longest=max(longest,current)
            if longest>=max(3,int(.05*(b-a))):
                if 'cycle_interrupted_by_dwell' not in result['warnings']:result['warnings'].append('cycle_interrupted_by_dwell')
                continue
            xs=np.concatenate(([ref],x[a+1:b+1],[ref]));fs=np.concatenate(([fa],f[a+1:b+1],[fb]))
            result['cycle_work_j'].append(float(np.trapezoid(fs,xs)))
    if not result['cycle_work_j']:result['warnings'].append('complete_synchronized_cycle_work_unavailable')
    return result
