# Strict TDD Evidence

This repository was updated in **STRICT TDD MODE** with `pytest`.

## Cycle followed

1. **Safety net**: ran the existing suite first (`pytest`) and confirmed `8 passed` before touching production code.
2. **RED**: added failing tests for architecture scaffolding, router/service behavior, manifest semantics, and `.engram` config.
3. **GREEN**: implemented the minimum adapters, service routing, error handling, and manifest/config fixes required to satisfy the verifier findings.
4. **REFACTOR**: extracted orchestration into service classes and thin spec-aligned adapter modules without rewriting stable heuristic logic.

## Commands used

- `pytest`
- `pytest tests/unit/test_services_and_architecture.py tests/integration/test_api.py tests/validation/test_runtime_scaffolding.py`
- `pytest --cov=src/digital_twin_lab --cov-report=term-missing`

## TDD rules enforced

- Tests were written before new production modules/services.
- Existing working endpoints were protected by the safety-net run.
- New behaviors include triangulation via happy-path + error-path assertions.
- Coverage execution was enabled by adding `pytest-cov` support in project config and environment.
