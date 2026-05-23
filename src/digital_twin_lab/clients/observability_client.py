from __future__ import annotations

from digital_twin_lab.config import settings


class ObservabilityClient:
    def health(self) -> dict[str, object]:
        return {"configured": bool(settings.observability_url), "url": settings.observability_url or None}
