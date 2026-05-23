from __future__ import annotations


class MetricsRegistry:
    def __init__(self) -> None:
        self.requests_total = 0

    def increment_requests(self) -> None:
        self.requests_total += 1


metrics_registry = MetricsRegistry()
