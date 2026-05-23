from __future__ import annotations

from digital_twin_lab.config import settings


class DocumentationClient:
    def health(self) -> dict[str, object]:
        return {"configured": bool(settings.documentation_url), "url": settings.documentation_url or None}
