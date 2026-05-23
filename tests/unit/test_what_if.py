from digital_twin_lab.risk.risk_classifier import RiskClassifier
from digital_twin_lab.setup.setup_diff import SetupDiff


def test_setup_diff_reports_changed_parameters_only():
    diff = SetupDiff.from_setups(
        baseline={"front_rebound": 8, "rear_rebound": 10, "engine_map": "mapping_1"},
        proposed={"front_rebound": 9, "rear_rebound": 10, "engine_map": "mapping_2"},
    )

    assert diff.changed_parameters == {
        "front_rebound": {"baseline": 8, "proposed": 9, "delta": 1},
        "engine_map": {"baseline": "mapping_1", "proposed": "mapping_2", "delta": "mapping_2"},
    }


def test_risk_classifier_distinguishes_safe_and_unsafe_metric_profiles():
    classifier = RiskClassifier()

    safe = classifier.classify(
        delta_metrics={"lap_time_delta_s": -0.12, "stability_score_delta": 0.08, "rear_temp_delta_c": -2.4},
        context={"component": "setup"},
    )
    unsafe = classifier.classify(
        delta_metrics={"lap_time_delta_s": 0.28, "stability_score_delta": -0.16, "rear_temp_delta_c": 7.2},
        context={"component": "part"},
    )

    assert safe.level == "low"
    assert safe.approval_required is False
    assert unsafe.level in {"high", "critical"}
    assert unsafe.approval_required is True
