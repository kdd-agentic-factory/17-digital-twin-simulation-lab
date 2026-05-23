from __future__ import annotations

from digital_twin_lab.config import settings


class RaceCommandClient:
    def health(self) -> dict[str, object]:
        return {"configured": bool(settings.race_command_url), "url": settings.race_command_url or None}
