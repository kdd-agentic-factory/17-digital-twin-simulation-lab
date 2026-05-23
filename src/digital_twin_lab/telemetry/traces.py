from __future__ import annotations

from digital_twin_lab.utils.ids import make_id


def create_trace_id() -> str:
    return make_id("trace")
