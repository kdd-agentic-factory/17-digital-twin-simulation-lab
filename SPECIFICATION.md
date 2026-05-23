# Specification: 17-digital-twin-simulation-lab

## 1. Propósito general del repositorio
Este repositorio implementa el laboratorio de simulación y gemelo digital del ecosistema. Su objetivo es validar de forma controlada las recomendaciones técnicas antes de elevarlas al crew chief o incorporarlas al Race Command Center.

La función principal del repositorio es simular escenarios como:
- cambios de setup,
- cambios de mapa motor,
- cambios de control de tracción,
- cambios de presión de neumáticos,
- evolución de degradación del neumático,
- comportamiento por curva,
- impacto de piezas específicas por circuito,
- riesgo térmico,
- riesgo de spin,
- riesgo de inestabilidad,
- impacto estimado sobre tiempo por vuelta.

La idea clave es: No toda recomendación debe ir directamente al crew chief. Primero debe pasar por una simulación, una clasificación de riesgo y una explicación trazable.

## 2. Papel dentro de la organización completa
`17-digital-twin-simulation-lab` se sitúa como capa de validación técnica y predictiva.

## 3. Responsabilidad principal
Debe responder a preguntas como:
- ¿Qué pasaría si cambiamos a Mapping 2 desde la vuelta 10?
- Qué ocurre si subimos 2 clicks el rear rebound?
- Qué impacto tiene bajar la presión trasera?
- Qué riesgo tiene montar un rear tire cooling duct?
- Qué pieza específica mejora la estabilidad en una curva rápida?
- Qué setup reduce el spin sin perder demasiada aceleración?
- Cuántas vueltas quedan antes del colapso del neumático?
- Qué curva concentra el mayor riesgo?
- Qué recomendación debería bloquearse por riesgo alto?

## 4. Tipo de sistema recomendado
FastAPI, Pydantic, NumPy, Pandas, SciPy, Scikit-learn, SimPy opcional, WebSocket/SSE opcional.

Módulos separados para: scenario definition, vehicle model simplificado, tire degradation model, setup impact model, part impact model, risk classifier, what-if runner, simulation report generator, evidence exporter.

## 5. Principios técnicos
- Simulación explicable antes que simulación opaca.
- Comparación baseline vs proposed.
- Simulación por curva.
- Separación entre predicción y decisión.
- Compatibilidad con datos sintéticos y reales.

## 6. Casos de uso principales
- What-if de mapa motor.
- What-if de suspensión.
- Predicción de colapso de neumático.
- Simulación de pieza específica.
- Comparación de setups.
- Validación de recomendación del Copilot.

## 7. Estructura final del repositorio
```text
17-digital-twin-simulation-lab/
│
├── README.md
├── AGENTS.md
├── Dockerfile
├── docker-compose.override.yml
├── pyproject.toml
├── .env.example
├── Makefile
│
├── src/
│   └── digital_twin_lab/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── constants.py
│       │
│       ├── models/
│       │   ├── scenario.py
│       │   ├── simulation.py
│       │   ├── setup.py
│       │   ├── part.py
│       │   ├── tire.py
│       │   ├── circuit.py
│       │   ├── telemetry.py
│       │   ├── risk.py
│       │   ├── recommendation.py
│       │   └── report.py
│       │
│       ├── simulation/
│       │   ├── scenario_runner.py
│       │   ├── simulation_engine.py
│       │   ├── baseline_comparator.py
│       │   ├── monte_carlo_runner.py
│       │   ├── sensitivity_analyzer.py
│       │   ├── uncertainty_estimator.py
│       │   └── result_builder.py
│       │
│       ├── vehicle/
│       │   ├── simplified_vehicle_model.py
│       │   ├── longitudinal_model.py
│       │   ├── lateral_model.py
│       │   ├── load_transfer_model.py
│       │   ├── suspension_model.py
│       │   └── engine_map_model.py
│       │
│       ├── tire/
│       │   ├── tire_degradation_model.py
│       │   ├── tire_thermal_model.py
│       │   ├── spin_model.py
│       │   ├── grip_model.py
│       │   └── collapse_predictor.py
│       │
│       ├── circuit/
│       │   ├── circuit_profile_loader.py
│       │   ├── corner_segmenter.py
│       │   ├── corner_phase_model.py
│       │   └── track_risk_model.py
│       │
│       ├── setup/
│       │   ├── setup_diff.py
│       │   ├── setup_impact_model.py
│       │   ├── setup_risk_model.py
│       │   └── setup_recommendation_validator.py
│       │
│       ├── parts/
│       │   ├── part_impact_model.py
│       │   ├── aero_part_model.py
│       │   ├── cooling_part_model.py
│       │   ├── part_risk_model.py
│       │   └── part_validation_service.py
│       │
│       ├── risk/
│       │   ├── risk_classifier.py
│       │   ├── unsafe_recommendation_blocker.py
│       │   ├── approval_requirement_detector.py
│       │   └── risk_explanation_builder.py
│       │
│       ├── clients/
│       │   ├── kdd_pipelines_client.py
│       │   ├── race_command_client.py
│       │   ├── documentation_client.py
│       │   ├── security_policy_client.py
│       │   └── observability_client.py
│       │
│       ├── routers/
│       │   ├── health.py
│       │   ├── scenarios.py
│       │   ├── simulations.py
│       │   ├── what_if.py
│       │   ├── setup.py
│       │   ├── tires.py
│       │   ├── parts.py
│       │   ├── recommendations.py
│       │   └── reports.py
│       │
│       ├── services/
│       │   ├── scenario_service.py
│       │   ├── simulation_service.py
│       │   ├── what_if_service.py
│       │   ├── tire_prediction_service.py
│       │   ├── setup_validation_service.py
│       │   ├── part_simulation_service.py
│       │   ├── recommendation_validation_service.py
│       │   └── report_service.py
│       │
│       ├── data/
│       │   ├── circuit_profiles/
│       │   │   ├── jerez.yaml
│       │   │   ├── mugello.yaml
│       │   │   └── assen.yaml
│       │   │
│       │   ├── baseline_setups/
│       │   │   ├── jerez-baseline.yaml
│       │   │   └── mugello-baseline.yaml
│       │   │
│       │   ├── tire_models/
│       │   │   ├── soft.yaml
│       │   │   ├── medium.yaml
│       │   │   └── hard.yaml
│       │   │
│       │   └── part_models/
│       │   │   ├── rear-tire-cooling-duct.yaml
│       │   │   ├── low-drag-side-deflector.yaml
│       │   │   └── brake-duct-insert.yaml
│       │
│       ├── telemetry/
│       │   ├── metrics.py
│       │   ├── traces.py
│       │   ├── logs.py
│       │   └── middleware.py
│       │
│       └── utils/
│           ├── ids.py
│           ├── time.py
│           ├── math.py
│           ├── risk.py
│           └── errors.py
│
├── experiments/
│   ├── README.md
│   ├── scenarios/
│   ├── results/
│   └── notebooks/
│
├── shared/
│   ├── schemas/
│   └── contracts/
│
├── docs/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── k8s/
│
└── .github/
```

## 8. Modelos principales
(Contenido de modelos: scenario.py, simulation.py, tire.py, risk.py)

## 9. Motor de simulación (simulation_engine.py)
## 10. Modelo de degradación de neumático
## 11. Setup impact model
## 12. Part impact model
## 13. Risk classifier
## 14. API principal (main.py)
## 15. Escenario ejemplo
## 16. Circuit profile example
## 17. Part model example
## 18. Variables de entorno
## 19. Dockerfile
## 20. Kubernetes
## 21. Observabilidad
## 22. Integración con el Copilot
## 23. Integración con Race Command Center
## 24. Integración con Experimentation Lab
## 25. Tests mínimos
## 26. Primeros ficheros que debes implementar
## 27. MVP funcional del repositorio 17
## 28. Criterios de aceptación
## 29. Riesgos técnicos
## 30. Relación con el paper
## 31. Resumen técnico
## 32. Decisión experta
```