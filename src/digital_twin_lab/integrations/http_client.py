from __future__ import annotations

import httpx


class IntegrationClient:
    def __init__(self, base_url: str, timeout_s: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def post_json(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
