import math
import pytest
from digital_twin_lab.chassis.signal_models import SignalSeries
from digital_twin_lab.chassis.suspension_signals import inspect_signal, movement_metrics


def series(times, values=None):
    return SignalSeries(times_s=times, values=values or [math.sin(t) for t in times], unit='m', sensor_id='suspension_front', provenance={})


def test_original_clock_quality():
    s = series([i*.01 for i in range(1000)])
    q = inspect_signal(s)
    assert q.status == 'eligible'
    assert q.effective_fs_hz == pytest.approx(100)
    for jitter, eligible in [(0.01, True), (.011, False)]:
        times = [0, .01, .02, .03 + .01*jitter, .04 + .01*jitter, .05 + .01*jitter]
        assert (inspect_signal(series(times)).status == 'eligible') == eligible


def test_quality_does_not_repair_samples():
    for ts, vs, reason in [([0,.01,.01],[1,2,3],'non_increasing_clock'),([0,.01,.02,.05],[1,2,3,4],'clock_gap'),([0,.01,.02],[1,float('nan'),3],'nonfinite_sample')]:
        s = series(ts,vs)
        q = inspect_signal(s)
        assert q.status == 'blocked' and reason in q.reasons
        assert s.times_s == ts


def test_movement_without_force_has_no_damping():
    s=series([i*.01 for i in range(1000)])
    result=movement_metrics(s,None)
    assert result['sample_count']==1000
    assert result['force_status']=='not_measured'
    assert result['velocity_status']=='not_available'
    assert 'hydraulic_force_n' not in result
