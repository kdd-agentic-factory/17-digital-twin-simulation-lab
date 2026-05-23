from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/baselines")
def list_baselines() -> dict[str, object]:
    return {"items": ["jerez-baseline", "mugello-baseline"]}
