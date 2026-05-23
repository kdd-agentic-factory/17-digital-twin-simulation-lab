from fastapi.testclient import TestClient

from digital_twin_lab.main import app


client = TestClient(app)


def test_health_endpoint_returns_service_status():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "digital-twin-lab"
    assert payload["telemetry"]["metrics_enabled"] is True


def test_what_if_endpoint_returns_explainable_baseline_comparison():
    response = client.post(
        "/what-if",
        json={
            "scenario_id": "jerez-map2-rebound",
            "circuit_id": "jerez",
            "session_id": "race",
            "baseline_setup_id": "jerez-baseline",
            "proposed_setup": {
                "front_rebound": 9,
                "rear_rebound": 11,
                "rear_ride_height_mm": 47,
                "engine_map": "mapping_2"
            },
            "laps": 12,
            "ambient_temp_c": 31.0,
            "track_temp_c": 41.0,
            "tire_compound": "soft"
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == "jerez-map2-rebound"
    assert payload["risk_level"] == "low"
    assert payload["approval_required"] is False
    assert payload["delta_metrics"]["lap_time_delta_s"] < 0
    assert payload["baseline_metrics"]["stability_score"] < payload["proposed_metrics"]["stability_score"]
    assert payload["explanation"]
    assert len(payload["limitations"]) >= 2


def test_parts_simulate_endpoint_returns_part_impact_and_risk():
    response = client.post(
        "/parts/simulate",
        json={
            "scenario_id": "mugello-side-deflector",
            "circuit_id": "mugello",
            "part_id": "low-drag-side-deflector",
            "installation_confidence": 0.91,
            "ambient_temp_c": 29.0,
            "track_temp_c": 44.0
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["part_id"] == "low-drag-side-deflector"
    assert payload["impact"]["top_speed_delta_kph"] > 0
    assert payload["impact"]["stability_delta"] < 0
    assert payload["risk_level"] in {"medium", "high"}
    assert payload["approval_required"] is True


def test_tires_predict_collapse_endpoint_returns_collapse_projection():
    response = client.post(
        "/tires/predict-collapse",
        json={
            "tire_id": "rear-soft-stint-01",
            "compound": "soft",
            "circuit_id": "jerez",
            "current_wear_pct": 71.0,
            "current_carcass_temp_c": 116.0,
            "stint_laps": 7,
            "ambient_temp_c": 33.0,
            "track_temp_c": 47.0,
            "aggression_index": 0.72
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tire_id"] == "rear-soft-stint-01"
    assert payload["degradation_index"] > 0.8
    assert payload["collapse_prediction"]["will_collapse"] is True
    assert payload["collapse_prediction"]["predicted_lap"] >= 1
    assert payload["risk_level"] in {"high", "critical"}


def test_recommendations_validate_endpoint_blocks_unsafe_changes():
    response = client.post(
        "/recommendations/validate",
        json={
            "recommendation_id": "rec-unsafe-1",
            "scenario_id": "assen-cooling-duct",
            "circuit_id": "assen",
            "baseline_setup_id": "jerez-baseline",
            "recommendation": {
                "target_component": "part",
                "action": "install",
                "value": "rear-tire-cooling-duct",
                "reasoning": "Reduce carcass temperature on exit",
                "confidence_score": 0.82,
                "risk_level": "low",
                "expected_impact": "rear_temp_delta_-6C"
            },
            "simulation_input": {
                "laps": 10,
                "ambient_temp_c": 22.0,
                "track_temp_c": 26.0,
                "tire_compound": "soft"
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation_id"] == "rec-unsafe-1"
    assert payload["allowed"] is False
    assert payload["blocked"] is True
    assert payload["risk_level"] in {"high", "critical"}
    assert payload["approval_required"] is True
    assert payload["reasons"]


def test_what_if_endpoint_rejects_invalid_payload_with_422():
    response = client.post(
        "/what-if",
        json={
            "scenario_id": "invalid-laps",
            "circuit_id": "jerez",
            "session_id": "race",
            "baseline_setup_id": "jerez-baseline",
            "proposed_setup": {},
            "laps": 0,
            "ambient_temp_c": 31.0,
            "track_temp_c": 41.0,
            "tire_compound": "soft",
        },
    )

    assert response.status_code == 422


def test_scenarios_endpoint_returns_catalog_backed_entries_and_detail():
    list_response = client.get("/scenarios")

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["items"]
    assert any(item["scenario_id"] == "jerez-map2-rebound" for item in list_payload["items"])

    detail_response = client.get("/scenarios/jerez-map2-rebound")

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["scenario_id"] == "jerez-map2-rebound"
    assert detail_payload["baseline_setup_id"] == "jerez-baseline"


def test_scenarios_endpoint_returns_404_for_unknown_catalog_id():
    response = client.get("/scenarios/unknown-scenario")

    assert response.status_code == 404
    assert response.json()["detail"] == "Scenario not found: unknown-scenario"


def test_simulations_and_latest_report_endpoints_return_mvp_payloads():
    simulations_response = client.get("/simulations")

    assert simulations_response.status_code == 200
    simulations_payload = simulations_response.json()
    assert simulations_payload["items"]
    assert simulations_payload["items"][0]["scenario_id"]
    assert simulations_payload["items"][0]["risk_classification"]["level"]

    report_response = client.get("/reports/latest")

    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["report_id"]
    assert report_payload["summary"]["scenario_id"]
    assert report_payload["key_findings"]


def test_parts_catalog_endpoint_returns_404_for_unknown_part_id():
    response = client.get("/parts/catalog/unknown-part")

    assert response.status_code == 404
    assert response.json()["detail"] == "Part not found: unknown-part"
