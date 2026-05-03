# 17-digital-twin-simulation-lab

Laboratorio de gemelo digital y simulacion para validar hipotesis antes de
llevar cambios a pista. Este repositorio se conecta conceptualmente con:

- `15-race-command-center`: observa, decide y opera.
- `16-race-ai-copilot`: conversa, interpreta y recomienda.

La pregunta que responde esta capa es:

> Que pasaria si probamos este cambio antes de ejecutarlo?

## Objetivo

Simular escenarios pre-Gran Premio y post-sesion para evaluar:

- cambios de setup
- mapas de motor
- presion de neumaticos
- geometria y suspension
- degradacion termica
- piezas aerodinamicas especificas
- estrategias por vuelta
- respuesta de la moto curva a curva

## Flujo operacional

```text
Telemetria real
-> deteccion de patron
-> recomendacion del copiloto
-> validacion en gemelo digital
-> aprobacion del crew chief
-> aplicacion en pista
-> nueva telemetria
-> aprendizaje
```

Ejemplo:

```text
16-race-ai-copilot
-> 01-agent-orchestrator
-> 17-digital-twin-simulation-lab
-> 15-race-command-center
-> informe con evidencia
```

## Inicio rapido

```powershell
python -m pip install -e ".[dev]"
python -m pytest
uvicorn digital_twin_simulation_lab.api.app:app --reload --port 8017
```

## API principal

`POST /v1/simulations/what-if`

```json
{
  "scenario_id": "qatar-race-l10-map2-rebound",
  "circuit": "Losail",
  "session": "race",
  "base_lap_time_s": 113.42,
  "laps": 22,
  "changes": {
    "rear_rebound_clicks": 2,
    "engine_map": "mapping_2",
    "apply_from_lap": 10
  },
  "baseline": {
    "rear_carcass_temp_c": 112.0,
    "rear_pressure_bar": 1.72,
    "spin_t05_pct": 18.0
  }
}
```

Respuesta resumida:

```json
{
  "scenario_id": "qatar-race-l10-map2-rebound",
  "risk": "medium-low",
  "recommendation": "Apply Mapping 2 from lap 10 and increase rear rebound by 2 clicks, subject to crew chief approval.",
  "summary": {
    "spin_t05_delta_pct": -7.8,
    "rear_carcass_temp_delta_c": -4.2,
    "lap_time_delta_s": 0.04,
    "degradation_delay_laps": 3
  }
}
```

## Estructura

```text
apps/                         UI futura del laboratorio
services/                     puntos de entrada por capacidad
domain/                       vocabulario y entidades de dominio
models/                       familias de modelos fisicos/ML
scenarios/                    escenarios predefinidos por sesion
integrations/                 clientes hacia repos y plataformas externas
data-contracts/               esquemas YAML versionados
workflows/                    flujos declarativos de simulacion
reports/                      plantillas y salidas generadas
k8s/                          manifiestos Kubernetes
src/digital_twin_simulation_lab/ motor Python inicial
tests/                        pruebas unitarias, integracion y validacion
```
