# Digital Twin Simulation Lab

FastAPI MVP para validar cambios de setup, piezas y riesgo antes de escalar una recomendacion al crew chief.

## Endpoints MVP

- `GET /health`
- `POST /what-if`
- `POST /parts/simulate`
- `POST /tires/predict-collapse`
- `POST /recommendations/validate`

## Run local

```powershell
python -m pip install -e .
python -m pytest tests/integration/test_api.py tests/unit/test_what_if.py tests/validation/test_contract_examples.py
uvicorn digital_twin_lab.main:app --reload --port 8017
```

## Example request

```json
{
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
}
```

## Architecture notes

- `src/digital_twin_lab/main.py` is the only FastAPI entrypoint.
- `routers/` exposes transport concerns only.
- `setup/`, `parts/`, and `risk/` hold deterministic explainable models for the MVP.
- `data/` contains YAML-backed catalog inputs so the app works with `PYTHONPATH=src` and no external services.
