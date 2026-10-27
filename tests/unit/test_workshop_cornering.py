import importlib
import importlib.util
import math
import pytest
from pydantic import ValidationError


def module():
    assert importlib.util.find_spec('digital_twin_lab.chassis.cornering'), 'Cornering model missing'
    return importlib.import_module('digital_twin_lab.chassis.cornering')


def test_cornering_image_is_a_synthetic_force_calculation_not_a_tire_diagnosis():
    m=module();body=m.CorneringInput(speed_m_s=185/3.6,radius_m=140,mass_kg=240)
    result=m.evaluate_cornering(body)
    assert result['metrics']['lateral_acceleration_m_s2']==pytest.approx((185/3.6)**2/140)
    assert result['metrics']['lateral_force_n']==pytest.approx(4527.1164021164)
    assert result['metrics']['combined_lean_rad']==pytest.approx(math.atan2((185/3.6)**2/140,9.80665))
    assert result['envelope']['status']=='missing_inputs'
    assert 'tire_saturation' not in result['metrics']


def test_mass_does_not_change_ideal_lean_and_unknown_fx_is_not_assumed_zero():
    m=module()
    a=m.evaluate_cornering(m.CorneringInput(speed_m_s=20,radius_m=40,mass_kg=100,mu_x=1,mu_y=1,derive_normal_load=True))
    b=m.evaluate_cornering(m.CorneringInput(speed_m_s=20,radius_m=40,mass_kg=200))
    assert b['metrics']['lateral_force_n']==2*a['metrics']['lateral_force_n']
    assert b['metrics']['combined_lean_rad']==a['metrics']['combined_lean_rad']
    assert 'longitudinal_force_n' in a['envelope']['missing']


def test_ellipse_retains_demand_above_one_and_is_symmetric():
    m=module()
    for fx in (-1000,1000):
        result=m.evaluate_cornering(m.CorneringInput(speed_m_s=20,radius_m=20,mass_kg=100,longitudinal_force_n=fx,normal_force_n=1000,mu_x=1,mu_y=1))
        assert result['envelope']['demand_ratio']==pytest.approx(math.sqrt(5))
        assert result['envelope']['label']=='idealized_friction_ellipse'
        assert 'low_side' not in str(result)


def test_invalid_inputs_and_hypotheses_do_not_generate_false_angles():
    m=module()
    for key,value in [('radius_m',0),('mass_kg',-1),('speed_m_s',float('nan')),('mu_x',0)]:
        data=dict(speed_m_s=20,radius_m=40,mass_kg=100);data[key]=value
        with pytest.raises(ValidationError):
            m.CorneringInput(**data)
    result=m.evaluate_cornering(m.CorneringInput(speed_m_s=0,radius_m=40,mass_kg=100,aero_hypothesis_n=180,rider_hanging_pct=65))
    assert result['metrics']['combined_lean_rad']==0
    assert 'aero_and_posture_not_modelled' in result['warnings']
    assert m.evaluate_cornering(m.CorneringInput(speed_m_s=1e308,radius_m=1,mass_kg=100))['status']=='out_of_domain'
