from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from digital_twin_lab.telemetry.metrics import metrics_registry
from digital_twin_lab.telemetry.traces import create_trace_id


class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        metrics_registry.increment_requests()
        response = await call_next(request)
        response.headers["X-Trace-Id"] = create_trace_id()
        return response
