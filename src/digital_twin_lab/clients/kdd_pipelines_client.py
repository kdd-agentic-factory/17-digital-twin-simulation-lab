from __future__ import annotations

from digital_twin_lab.config import settings


class KddPipelinesClient:
    def health(self) -> dict[str, object]:
        return {"configured": bool(settings.pipelines_url), "url": settings.pipelines_url or None}
