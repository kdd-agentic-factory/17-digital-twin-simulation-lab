import math
import numpy as np
import pytest
from digital_twin_lab.chassis.signal_models import SignalSeries, BenchConditions
from digital_twin_lab.chassis.suspension_bench import bench_curves


def measured():
    t=np.arange(0,5,.001);x=.01*np.sin(2*np.pi*t);v=.01*2*np.pi*np.cos(2*np.pi*t)
    def s(values,unit):return SignalSeries(t.tolist(),values.tolist(),unit,'suspension_rear',{})
    return s(v*1000,'N'),s(x,'m'),s(v,'m/s')


def test_closed_cycle_work_matches_analytic_integral():
    f,x,v=measured()
    result=bench_curves(f,x,v,BenchConditions(synchronization_reference='shared-clock',work_convention='force_along_positive_displacement'))
    assert len(result['cycle_work_j'])>=3
    assert result['cycle_work_j'][0]==pytest.approx(math.pi*1000*.01**2*(2*math.pi),rel=.01)


def test_total_force_never_labelled_hydraulic():
    f,x,v=measured();r=bench_curves(f,x,v,BenchConditions())
    assert r['force_definition']=='total_measured'
    assert r['temperature_c'] is None
    assert 'hydraulic_force_n' not in r
    assert r['cycle_work_j']==[]


def test_incomplete_or_desynchronized_cycle_has_no_work():
    f,x,v=measured()
    assert bench_curves(f,x,v,BenchConditions())['cycle_work_j']==[]
    x2=SignalSeries([t+.001 for t in x.times_s],x.values,'m','suspension_rear',{})
    with pytest.raises(ValueError,match='synchron'):bench_curves(f,x2,v,BenchConditions())


def test_velocity_only_has_no_cycle_energy():
    f,x,v=measured()
    assert bench_curves(f,None,v,BenchConditions())['cycle_work_j']==[]


def test_separate_pulses_are_not_a_complete_cycle():
    t=np.arange(0,4,.01);x=np.zeros(len(t))
    for start in (30,230):x[start:start+40]=np.r_[np.linspace(0,1,20),np.linspace(1,0,20)]
    velocity=np.gradient(x,.01)
    def s(values,unit):return SignalSeries(t.tolist(),values.tolist(),unit,'suspension_rear',{})
    r=bench_curves(s(3*velocity,'N'),s(x,'m'),s(velocity,'m/s'),BenchConditions(synchronization_reference='same clock',work_convention='force_along_positive_displacement'))
    assert r['cycle_work_j']==[]
    assert 'cycle_interrupted_by_dwell' in r['warnings']
