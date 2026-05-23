"""Helpers for stable identifiers."""

from __future__ import annotations

import re
from uuid import uuid4


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "item"


def make_id(prefix: str, seed: str | None = None) -> str:
    if seed:
        return f"{prefix}-{slugify(seed)}"
    return f"{prefix}-{uuid4().hex[:8]}"
