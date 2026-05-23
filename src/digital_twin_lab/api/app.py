"""Digital Twin Simulation Lab — FastAPI entry point."""
from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from digital_twin_lab.domain import SimulationResult, SimulationScenario
from digital_twin_lab.simulators import run_what_if

logger = logging.getLogger(__name__)

VERSION = "0.1.0"

# Optional Redpanda/Kafka producer for simulation.results topic
_producer = None


def _try_init_producer():
    global _producer
    broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
    try:
        from kafka import KafkaProducer
        _producer = KafkaProducer(
            bootstrap_servers=broker,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        logger.info("Redpanda producer ready (simulation.results → %s)", broker)
    except Exception as exc:
        logger.warning("Redpanda producer unavailable (%s) — results will not stream", exc)


async def _publish_result(result: SimulationResult) -> None:
    if _producer is None:
        return
    try:
        _producer.send("simulation.results", result.model_dump())
    except Exception as exc:
        logger.debug("Failed to publish simulation result: %s", exc)


@asynccontextmanager
async def lifespan(application: FastAPI):
    _try_init_producer()
    logger.info("Digital Twin Simulation Lab v%s started", VERSION)
    yield
    if _producer:
        _producer.close()
    logger.info("Digital Twin Simulation Lab stopped")


app = FastAPI(
    title="Digital Twin Simulation Lab",
    version=VERSION,
    description="What-if simulation API for race setup, tire, engine map and strategy hypotheses.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "digital-twin-simulation-lab", "version": VERSION}


@app.get("/version")
def version() -> dict:
    return {"service": "digital-twin-simulation-lab", "version": VERSION}


@app.post("/v1/simulations/what-if", response_model=SimulationResult)
async def simulate_what_if(scenario: SimulationScenario) -> SimulationResult:
    result = run_what_if(scenario)
    await _publish_result(result)
    return result
