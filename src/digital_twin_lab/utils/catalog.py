"""YAML catalog loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from digital_twin_lab.config import settings
from digital_twin_lab.utils.errors import ResourceNotFoundError


class Catalog:
    def __init__(self, data_dir: str | None = None) -> None:
        self._data_dir = Path(data_dir or settings.data_dir)

    def load(self, *parts: str) -> dict[str, Any]:
        file_path = self._data_dir.joinpath(*parts)
        if not file_path.exists():
            raise ResourceNotFoundError(f"Catalog file not found: {'/'.join(parts)}")
        return yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
