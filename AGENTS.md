# AGENTS.md

## Proposito del repositorio

Este repositorio implementa el laboratorio de gemelo digital y simulacion para
validar cambios antes de aplicarlos en pista. El sistema debe producir evidencia
accionable para el Race Command Center y el AI Copilot.

## Principios de trabajo

- Mantener las simulaciones deterministas por defecto.
- Separar dominio, modelos, escenarios, integraciones y API.
- Versionar contratos de entrada/salida en `data-contracts/`.
- Documentar supuestos fisicos cuando un modelo sea heuristico.
- No bloquear la ejecucion local por dependencias externas.

## Calidad esperada

- Toda logica nueva debe tener pruebas unitarias o de validacion.
- Las respuestas de simulacion deben incluir riesgo, recomendacion y metricas.
- Los clientes externos deben tener interfaces claras y fallar de forma
  controlada cuando no haya endpoints configurados.

## Comandos utiles

```powershell
python -m pip install -e ".[dev]"
python -m pytest
uvicorn digital_twin_simulation_lab.api.app:app --reload --port 8017
```
