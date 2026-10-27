import importlib
import importlib.util
import pytest
from test_workshop_pose import pose_input


def module():
    assert importlib.util.find_spec('digital_twin_lab.chassis.target_lock'), 'Target Lock solver missing'
    return importlib.import_module('digital_twin_lab.chassis.target_lock')


def test_target_lock_returns_no_change_when_already_at_target():
    m=module()
    from digital_twin_lab.chassis.planar_pose import PoseInput,evaluate_pose
    base=PoseInput(**pose_input());target=evaluate_pose(base).metrics
    request=m.TargetLockInput(base=base,target_rake_rad=target['rake_rad'],target_trail_m=target['trail_m'],rake_tolerance_rad=1e-7,trail_tolerance_m=1e-7,actuators=[])
    result=m.solve_target_lock(request)
    assert result['status']=='feasible' and result['changes']=={}


def test_target_lock_discrete_solution_recalculates_and_does_not_mutate_base():
    m=module()
    from digital_twin_lab.chassis.planar_pose import PoseInput,evaluate_pose
    base=PoseInput(**pose_input());before=base.model_dump()
    target=base.model_copy(deep=True);target.mechanical.fork_length_m.value=.32
    metrics=evaluate_pose(target,check_reference=False).metrics
    req=m.TargetLockInput(base=base,target_rake_rad=metrics['rake_rad'],target_trail_m=metrics['trail_m'],rake_tolerance_rad=1e-8,trail_tolerance_m=1e-8,actuators=[dict(key='fork_length_m',minimum=.3,maximum=.34,step=.01)])
    result=m.solve_target_lock(req)
    assert result['status']=='feasible'
    assert result['changes']['fork_length_m']==pytest.approx(.32)
    assert result['residuals']['trail_m']<1e-8
    assert result['candidate_metrics']['rake_rad']==pytest.approx(metrics['rake_rad'])
    assert base.model_dump()==before


def test_limits_are_not_reported_as_physical_infeasibility():
    m=module()
    request=m.TargetLockInput(base=pose_input(),target_rake_rad=.2,target_trail_m=.1,rake_tolerance_rad=1e-8,trail_tolerance_m=1e-8,actuators=[dict(key='fork_length_m',minimum=.2,maximum=.4,step=.000001)])
    result=m.solve_target_lock(request)
    assert result['status']=='out_of_domain' and result['reason']=='search_space_limit'
    assert result['evaluations']<=5000


def test_missing_and_infeasible_are_distinct():
    m=module()
    common=dict(target_rake_rad=.2,target_trail_m=.1,rake_tolerance_rad=1e-8,trail_tolerance_m=1e-8,actuators=[])
    assert m.solve_target_lock(m.TargetLockInput(base={'values':{}},**common))['status']=='missing_inputs'
    assert m.solve_target_lock(m.TargetLockInput(base=pose_input(),**common))['status']=='infeasible'
