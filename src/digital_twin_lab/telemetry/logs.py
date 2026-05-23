from __future__ import annotations

import logging

from digital_twin_lab.config import settings


def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
