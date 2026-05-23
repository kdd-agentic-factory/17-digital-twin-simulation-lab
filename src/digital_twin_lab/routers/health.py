from __future__ import annotations

from fastapi import APIRouter

from digital_twin_lab.clients import (
    DocumentationClient,
    KddPipelinesClient,
    ObservabilityClient,
    RaceCommandClient,
    SecurityPolicyClient,
)
from digital_twin_lab.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "telemetry": {"metrics_enabled": settings.metrics_enabled, "traces_enabled": settings.traces_enabled},
        "dependencies": {
            "race_command": RaceCommandClient().health(),
            "documentation": DocumentationClient().health(),
            "security_policy": SecurityPolicyClient().health(),
            "observability": ObservabilityClient().health(),
            "pipelines": KddPipelinesClient().health(),
        },
    }
