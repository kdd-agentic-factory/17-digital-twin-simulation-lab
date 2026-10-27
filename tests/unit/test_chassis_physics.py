import math
import pytest
from pydantic import ValidationError
from digital_twin_lab.chassis.models import MeasuredValue, SetupRevision
from digital_twin_lab.chassis.physics import evaluate_static, load_transfer, spring_response


def setup(**overrides):
    values = dict(front_radius_m=(.3, 'm'), rake_rad=(math.radians(24), 'rad'),
                  offset_m=(.03, 'm'), wheelbase_m=(1.4, 'm'), mass_kg=(200, 'kg'),
                  front_weight_fraction=(.5, '1'), cg_height_m=(.55, 'm'))
    values.update(overrides)
    return SetupRevision(id='a', bike_id='bike', version=1, values={
        k: MeasuredValue(value=v, unit=u, provenance='measured') for k, (v, u) in values.items()})


def test_static_geometry_and_normal_trail():
    r = evaluate_static(setup())
    assert r.metrics['trail_m'] == pytest.approx(.100729517237, abs=1e-10)
    assert r.metrics['normal_trail_m'] == pytest.approx(r.metrics['trail_m'] * math.cos(math.radians(24)))
    assert evaluate_static(setup(rake_rad=(0, 'rad'), offset_m=(0, 'm'))).metrics['trail_m'] == 0


def test_transfer_conserves_weight_and_sign():
    zero = load_transfer(setup(), 0).metrics
    assert zero['front_load_n'] == pytest.approx(980.665)
    for ax in [-3, 3]:
        r = load_transfer(setup(), ax).metrics
        assert r['front_load_n'] + r['rear_load_n'] == pytest.approx(1961.33)
        assert (r['front_load_n'] < zero['front_load_n']) == (ax > 0)


def test_contact_loss_is_invalid_without_clamping():
    r = load_transfer(setup(), 30)
    assert not r.metrics
    assert 'contact_loss' in r.warnings


def test_constant_and_variable_wheel_rate():
    assert spring_response(100000, .02, .01, .5, 0).metrics['wheel_rate_n_m'] == 25000
    assert spring_response(100000, .02, .01, .5, 2).metrics['wheel_rate_n_m'] == 31000


def test_missing_and_unknown_units_do_not_make_results():
    assert 'front_radius_m' in evaluate_static(setup(front_radius_m=(None, 'm'))).missing
    r = evaluate_static(setup(front_radius_m=(300, 'mm')))
    assert not r.metrics
    assert any('unit' in w for w in r.warnings)


@pytest.mark.parametrize('key,value', [('wheelbase_m', 0), ('rake_rad', math.pi / 2), ('mass_kg', -1)])
def test_out_of_domain(key, value):
    s = setup(**{key: (value, 'rad' if key == 'rake_rad' else 'kg' if key == 'mass_kg' else 'm')})
    r = evaluate_static(s) if key == 'rake_rad' else load_transfer(s, 0)
    assert not r.metrics
    assert r.warnings


def test_nonfinite_input_rejected_and_assumptions_visible():
    with pytest.raises(ValidationError):
        MeasuredValue(value=float('nan'), unit='m', provenance='measured')
    s = setup()
    s.values['front_radius_m'].provenance = 'assumed'
    assert 'assumed:front_radius_m' in evaluate_static(s).warnings


def test_finite_inputs_that_overflow_do_not_return_nonfinite_metrics():
    assert not load_transfer(setup(mass_kg=(1e308, 'kg')), 1e308).metrics
    assert not spring_response(1e308, 1e308, 1e308, 1e308, 1e308).metrics
