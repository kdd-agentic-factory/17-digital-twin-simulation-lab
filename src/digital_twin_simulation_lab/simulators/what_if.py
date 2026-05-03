from digital_twin_simulation_lab.domain import (
    SimulationResult,
    SimulationScenario,
    SimulationSummary,
)
from digital_twin_simulation_lab.simulators.engine_map import engine_map_effect
from digital_twin_simulation_lab.simulators.risk import classify_risk
from digital_twin_simulation_lab.simulators.suspension import rear_rebound_effect
from digital_twin_simulation_lab.simulators.tire import degradation_delay_laps, tire_pressure_effect


def run_what_if(scenario: SimulationScenario) -> SimulationResult:
    active_laps = max(0, scenario.laps - scenario.changes.apply_from_lap + 1)
    active_ratio = active_laps / scenario.laps

    rebound = rear_rebound_effect(scenario.changes.rear_rebound_clicks)
    pressure = tire_pressure_effect(scenario.changes.rear_pressure_delta_bar)
    engine = engine_map_effect(scenario.changes.engine_map)

    spin_delta = (rebound["spin_delta_pct"] + pressure["spin_delta_pct"]) * active_ratio
    if engine["torque_trim"] < 0:
        spin_delta += engine["torque_trim"] * 100.0 * active_ratio

    temp_delta = (
        rebound["temp_delta_c"] + pressure["temp_delta_c"] + engine["thermal_trim_c"]
    ) * active_ratio

    lap_delta = (
        rebound["lap_penalty_s"] + pressure["lap_penalty_s"] + engine["lap_penalty_s"]
    )

    delay = degradation_delay_laps(temp_delta, spin_delta)
    risk = classify_risk(temp_delta, spin_delta, lap_delta)

    recommendation = _build_recommendation(scenario, risk)
    evidence = [
        f"Change active for {active_laps} of {scenario.laps} laps.",
        f"Engine map {scenario.changes.engine_map} contributes {engine['thermal_trim_c']:.1f} C thermal trim.",
        f"Rear rebound change contributes {rebound['spin_delta_pct']:.1f}% spin delta before lap weighting.",
    ]

    return SimulationResult(
        scenario_id=scenario.scenario_id,
        risk=risk,
        recommendation=recommendation,
        summary=SimulationSummary(
            spin_t05_delta_pct=round(spin_delta, 1),
            rear_carcass_temp_delta_c=round(temp_delta, 1),
            lap_time_delta_s=round(lap_delta, 2),
            degradation_delay_laps=delay,
        ),
        evidence=evidence,
    )


def _build_recommendation(scenario: SimulationScenario, risk: str) -> str:
    changes = scenario.changes
    if risk == "high":
        return "Do not apply without additional validation and crew chief approval."

    actions: list[str] = []
    if changes.engine_map != "baseline":
        actions.append(f"apply {changes.engine_map.replace('_', ' ').title()} from lap {changes.apply_from_lap}")
    if changes.rear_rebound_clicks:
        direction = "increase" if changes.rear_rebound_clicks > 0 else "decrease"
        actions.append(f"{direction} rear rebound by {abs(changes.rear_rebound_clicks)} clicks")
    if changes.rear_pressure_delta_bar:
        direction = "raise" if changes.rear_pressure_delta_bar > 0 else "lower"
        actions.append(f"{direction} rear pressure by {abs(changes.rear_pressure_delta_bar):.2f} bar")

    if not actions:
        return "Keep baseline setup; no material change requested."

    return f"{' and '.join(actions).capitalize()}, subject to crew chief approval."
