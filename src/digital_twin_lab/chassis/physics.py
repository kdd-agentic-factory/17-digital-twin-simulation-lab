"""SI, upright/zero steer, level road, quasi-static and no aerodynamic forces."""
import math

from .models import PhysicsResult, SetupRevision

UNITS = {'front_radius_m': 'm', 'rake_rad': 'rad', 'offset_m': 'm',
         'wheelbase_m': 'm', 'mass_kg': 'kg', 'front_weight_fraction': '1', 'cg_height_m': 'm',
         'spring_rate_n_m': 'N/m', 'preload_m': 'm', 'motion_ratio': '1', 'motion_ratio_slope_per_m': '1/m'}


def inputs(setup: SetupRevision, keys: list[str]):
    result = PhysicsResult()
    values = {}
    for key in keys:
        item = setup.values.get(key)
        if item is None or item.value is None:
            result.missing.append(key)
        elif item.unit != UNITS[key]:
            result.warnings.append(f'invalid_unit:{key}:expected_{UNITS[key]}')
        else:
            values[key] = item.value
            if item.provenance == 'assumed':
                result.warnings.append(f'assumed:{key}')
    return result, values


def evaluate_static(setup: SetupRevision) -> PhysicsResult:
    result, v = inputs(setup, ['front_radius_m', 'rake_rad', 'offset_m'])
    if len(v) != 3:
        return result
    r, a, d = v['front_radius_m'], v['rake_rad'], v['offset_m']
    if not (0 < r <= 1 and 0 <= a < math.pi / 3 and 0 <= d < r):
        result.warnings.append('invalid_geometry_domain')
        return result
    trail = (r * math.sin(a) - d) / math.cos(a)
    result.metrics = {'trail_m': trail, 'normal_trail_m': trail * math.cos(a)}
    wheelbase = setup.values.get('wheelbase_m')
    if wheelbase and wheelbase.value is not None:
        if wheelbase.unit == 'm' and wheelbase.value > 0:
            result.metrics['wheelbase_m'] = wheelbase.value
        else:
            result.warnings.append('invalid_wheelbase')
    return result


def load_transfer(setup: SetupRevision, ax_m_s2: float) -> PhysicsResult:
    result, v = inputs(setup, ['mass_kg', 'front_weight_fraction', 'cg_height_m', 'wheelbase_m'])
    if len(v) != 4:
        return result
    m, f, h, length = (v[k] for k in ['mass_kg', 'front_weight_fraction', 'cg_height_m', 'wheelbase_m'])
    if not math.isfinite(ax_m_s2) or not (m > 0 and 0 < f < 1 and h > 0 and length > 0):
        result.warnings.append('invalid_load_domain')
        return result
    front = m * 9.80665 * f - m * ax_m_s2 * h / length
    rear = m * 9.80665 - front
    if not all(math.isfinite(x) for x in [front, rear]):
        result.warnings.append('load_overflow')
        return result
    if min(front, rear) < 0:
        result.warnings.append('contact_loss')
        return result
    result.metrics = {'front_load_n': front, 'rear_load_n': rear}
    return result


def spring_response(k_n_m: float, s_m: float, preload_m: float, q: float, dq_dz: float) -> PhysicsResult:
    result = PhysicsResult()
    if not all(math.isfinite(x) for x in [k_n_m, s_m, preload_m, q, dq_dz]) or min(k_n_m, q) <= 0 or min(s_m, preload_m) < 0:
        result.warnings.append('invalid_spring_domain')
        return result
    force = k_n_m * (s_m + preload_m)
    result.metrics = {'spring_force_n': force, 'wheel_force_n': force * q,
                      'wheel_rate_n_m': k_n_m * q * q + force * dq_dz}
    if not all(math.isfinite(x) for x in result.metrics.values()):
        result.metrics = {}
        result.warnings.append('spring_overflow')
    return result
