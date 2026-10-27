import importlib
import importlib.util
import pytest


def module():
    assert importlib.util.find_spec('digital_twin_lab.chassis.chain_geometry'), 'Chain geometry missing'
    return importlib.import_module('digital_twin_lab.chassis.chain_geometry')


def test_upper_tangent_and_intersection_analytic_cases():
    m=module()
    a,b=m.upper_tangent((0,0),(2,0),.1,.1)
    assert a == pytest.approx((0,.1)) and b == pytest.approx((2,.1))
    assert m.line_intersection((0,0),(1,1),(0,1),(1,0)) == pytest.approx((.5,.5))
    assert m.line_intersection((0,0),(1,0),(0,1),(1,1)) is None
    with pytest.raises(ValueError):
        m.upper_tangent((0,0),(.01,0),.1,.2)


def test_anti_squat_is_not_certified_by_a_geometric_ifc():
    m=module()
    result=m.evaluate_chain({},None)
    assert result['anti_squat_status']=='unavailable'
    assert 'anti_squat_pct' not in result['metrics']
