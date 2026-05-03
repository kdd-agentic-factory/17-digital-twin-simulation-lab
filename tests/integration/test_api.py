from fastapi.testclient import TestClient

from digital_twin_simulation_lab.api.app import app


def test_what_if_endpoint_returns_result():
    client = TestClient(app)
    response = client.post(
        "/v1/simulations/what-if",
        json={
            "scenario_id": "qatar-race-l10-map2-rebound",
            "circuit": "Losail",
            "session": "race",
            "base_lap_time_s": 113.42,
            "laps": 22,
            "changes": {
                "rear_rebound_clicks": 2,
                "engine_map": "mapping_2",
                "apply_from_lap": 10,
            },
            "baseline": {
                "rear_carcass_temp_c": 112.0,
                "rear_pressure_bar": 1.72,
                "spin_t05_pct": 18.0,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == "qatar-race-l10-map2-rebound"
    assert payload["risk"] == "medium-low"
    assert "crew chief" in payload["recommendation"]
