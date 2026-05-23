from __future__ import annotations

from digital_twin_lab.config import settings


class SecurityPolicyClient:
    def health(self) -> dict[str, object]:
        return {"configured": bool(settings.security_policy_url), "url": settings.security_policy_url or None}
