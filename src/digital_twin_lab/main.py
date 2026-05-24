from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


def _configure_otel(app: FastAPI, service_name: str = "digital-twin-simulation-lab") -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("OTEL setup failed (non-fatal): %s", exc)

from digital_twin_lab import __version__
from digital_twin_lab.config import settings
from digital_twin_lab.database import init_db
from digital_twin_lab.routers import all_routers
from digital_twin_lab.telemetry import TelemetryMiddleware, configure_logging
from digital_twin_lab.utils.errors import ResourceNotFoundError, ValidationError

_REQUEST_COUNT = Counter(
    "digital_twin_http_requests_total", "Total HTTP requests", ["method", "path", "status_code"]
)
_REQUEST_LATENCY = Histogram(
    "digital_twin_http_request_duration_seconds", "HTTP request duration", ["method", "path"]
)
_SIMULATION_COUNT = Counter(
    "digital_twin_simulations_total", "Simulations run", ["type", "circuit_id"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Digital Twin Simulation Lab",
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(TelemetryMiddleware)

    @app.exception_handler(ResourceNotFoundError)
    async def handle_not_found(_, exc: ResourceNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def handle_validation_error(_, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next):
        path = request.url.path
        method = request.method
        with _REQUEST_LATENCY.labels(method=method, path=path).time():
            response = await call_next(request)
        _REQUEST_COUNT.labels(method=method, path=path, status_code=response.status_code).inc()
        return response

    @app.get("/metrics", include_in_schema=False)
    async def _metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    for router in all_routers:
        app.include_router(router)
    _configure_otel(app)
    return app


app = create_app()
