from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from digital_twin_lab import __version__
from digital_twin_lab.config import settings
from digital_twin_lab.routers import all_routers
from digital_twin_lab.telemetry import TelemetryMiddleware, configure_logging
from digital_twin_lab.utils.errors import ResourceNotFoundError, ValidationError


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Digital Twin Simulation Lab", version=__version__)
    app.add_middleware(TelemetryMiddleware)

    @app.exception_handler(ResourceNotFoundError)
    async def handle_not_found(_, exc: ResourceNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def handle_validation_error(_, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    for router in all_routers:
        app.include_router(router)
    return app


app = create_app()
