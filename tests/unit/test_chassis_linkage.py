import math

import pytest
from pydantic import ValidationError

from digital_twin_lab.chassis.linkage import linkage_at_shock, progressive_response
from digital_twin_lab.chassis.models import LinkageCurve


def curve(z=(0, .05, .1), s=(0, .025, .05)):
    return LinkageCurve(points=[{'wheel_m':x, 'shock_m':y} for x,y in zip(z,s)], provenance='measured', reference='full_extension', source='QA bench fixture')


def test_linear_curve_matches_existing_wheel_rate():
    c = curve()
    position = linkage_at_shock(c,.02)
    assert position['wheel_m'] == pytest.approx(.04,abs=1e-9)
    assert position['q'] == pytest.approx(.5)
    assert position['dq_dz'] == pytest.approx(0,abs=1e-10)
    r = progressive_response(c,100000,.01,.02)
    assert r.metrics['wheel_force_n'] == pytest.approx(1500)
    assert r.metrics['wheel_rate_n_m'] == pytest.approx(25000)


@pytest.mark.parametrize('shock',[-.001,.051,float('nan')])
def test_outside_measured_curve_is_never_extrapolated(shock):
    assert not progressive_response(curve(),100000,.01,shock).metrics


@pytest.mark.parametrize('z,s', [([0,.05,.05],[0,.02,.03]), ([0,.05,.1],[0,.03,.02]), ([.01,.05,.1],[0,.02,.03]), ([0,.05,.1],[0,.02,float('inf')])])
def test_invalid_or_unreferenced_curve_rejected(z,s):
    with pytest.raises(ValidationError):
        curve(z,s)


def test_nodes_and_inverse_roundtrip_against_independent_scipy():
    scipy = pytest.importorskip('scipy.interpolate')
    z=[0,.03,.06,.09,.12]; s=[0,.012,.027,.045,.066]
    c=curve(z,s)
    reference=scipy.PchipInterpolator(z,s,extrapolate=False)
    for i in range(121):
        wheel=i*.001
        shock=float(reference(wheel))
        result=linkage_at_shock(c,shock)
        assert result['wheel_m'] == pytest.approx(wheel,abs=1e-9)
        assert result['q'] == pytest.approx(float(reference(wheel,1)),abs=1e-7)
        assert result['dq_dz'] == pytest.approx(float(reference(wheel,2)),abs=1e-5)
    node=linkage_at_shock(c,s[2])
    assert node['at_knot']
    assert math.isfinite(node['left_dq_dz'])
