import importlib
import importlib.util
import math

import pytest
from digital_twin_lab.chassis.workshop_models import MechanicalSetup


def measure(value, unit='m'):
    return dict(value=value, unit=unit, provenance='measured')


def pose_input():
    return dict(values={k:measure(v,u) for k,v,u in [('front_radius_m',.3,'m'),('rake_rad',math.atan(.2),'rad'),('offset_m',0,'m')]},
        mechanical=dict(points={'swingarm_pivot':dict(x=measure(0),z=measure(0)), 'steer_reference':dict(x=measure(1),z=measure(0))},
            rear_radius_m=measure(.3),swingarm_length_m=measure(.5),swingarm_angle_rad=measure(0,'rad'),steer_axis_body_rad=measure(0,'rad'),fork_length_m=measure(.3)))


def module():
    assert importlib.util.find_spec('digital_twin_lab.chassis.planar_pose'), 'Pose engine missing'
    return importlib.import_module('digital_twin_lab.chassis.planar_pose')


def test_world_rake_is_not_reinterpreted_as_body_axis():
    m=module()
    data=pose_input()
    del data['mechanical']['steer_axis_body_rad']
    result=m.evaluate_pose(m.PoseInput(**data))
    assert result.status=='missing_inputs'
    assert 'steer_axis_body_rad' in result.missing


def test_pose_rejects_inconsistent_world_rake():
    m=module()
    data=pose_input()
    data['mechanical']['steer_axis_body_rad']=measure(0,'rad')
    data['values']['rake_rad']=measure(0,'rad')
    result=m.evaluate_pose(m.PoseInput(**data))
    assert result.status=='inconsistent_inputs'
    assert 'world_rake_inconsistent_with_pose' in result.warnings
    assert not result.metrics


def test_pose_closes_ground_constraints_without_moving_dimensions():
    m = module()
    result = m.evaluate_pose(m.PoseInput(**pose_input()))
    assert result.status == 'available'
    assert result.points['rear_axle'] == pytest.approx([0,.3])
    assert result.points['front_axle'][1] == pytest.approx(.3)
    assert result.metrics['wheelbase_m'] == pytest.approx(math.hypot(1.5,.3))
    assert result.metrics['rake_rad'] == pytest.approx(math.atan(.2))
    assert result.metrics['trail_m'] == pytest.approx(.06)


def test_partial_and_invalid_pose_do_not_make_geometry():
    m = module()
    partial = m.evaluate_pose(m.PoseInput(values={},mechanical=MechanicalSetup()))
    assert partial.status == 'missing_inputs' and not partial.points
    data = pose_input()
    data['mechanical']['fork_compression_m'] = measure(.4)
    invalid = m.evaluate_pose(m.PoseInput(**data))
    assert invalid.status == 'out_of_domain' and not invalid.metrics


def test_assumed_coordinates_are_not_relabelled_as_measured():
    m = module()
    data=pose_input()
    data['mechanical']['rear_radius_m']['provenance']='assumed'
    assert 'assumed:rear_radius_m' in m.evaluate_pose(m.PoseInput(**data)).warnings
