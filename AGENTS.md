# AGENTS.md

## Repo intent

This repo is the deterministic MVP simulation gate for setup, tire and part recommendations.

## Non-negotiables

- Keep `PYTHONPATH=src` imports working.
- Prefer explainable heuristics over opaque ML for the MVP.
- Do not reintroduce legacy `api/`, `simulators/`, `integrations/`, or `domain.py` production entrypoints.
- Every new behavior needs pytest coverage first.

## Useful commands

```powershell
python -m pip install -e .
python -m pytest tests/integration/test_api.py tests/unit/test_what_if.py tests/validation/test_contract_examples.py
uvicorn digital_twin_lab.main:app --reload --port 8017
```
