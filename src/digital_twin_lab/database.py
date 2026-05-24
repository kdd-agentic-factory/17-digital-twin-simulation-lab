"""Async SQLAlchemy database layer — PostgreSQL in prod, SQLite for local dev."""

from __future__ import annotations

import json
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

logger = logging.getLogger(__name__)

_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./digital_twin.db",
)
if _DATABASE_URL.startswith("postgresql://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

_is_sqlite = _DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    _DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    poolclass=NullPool if _is_sqlite else AsyncAdaptedQueuePool,
    pool_pre_ping=not _is_sqlite,
    json_serializer=json.dumps,
    json_deserializer=json.loads,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_DDL = """
CREATE TABLE IF NOT EXISTS simulation_results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id  TEXT NOT NULL,
    result_json  TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_scenario ON simulation_results (scenario_id);

CREATE TABLE IF NOT EXISTS what_if_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id     TEXT NOT NULL,
    circuit_id      TEXT NOT NULL,
    session_id      TEXT,
    baseline_setup  TEXT NOT NULL,
    proposed_setup  TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_whatif_scenario ON what_if_results (scenario_id);

CREATE TABLE IF NOT EXISTS race_strategy_results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id  TEXT NOT NULL,
    circuit_id   TEXT NOT NULL,
    result_json  TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_strategy_circuit ON race_strategy_results (circuit_id);
"""

_DDL_PG = """
CREATE TABLE IF NOT EXISTS simulation_results (
    id           BIGSERIAL PRIMARY KEY,
    scenario_id  TEXT NOT NULL,
    result_json  JSONB NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_scenario ON simulation_results (scenario_id);

CREATE TABLE IF NOT EXISTS what_if_results (
    id              BIGSERIAL PRIMARY KEY,
    scenario_id     TEXT NOT NULL,
    circuit_id      TEXT NOT NULL,
    session_id      TEXT,
    baseline_setup  TEXT NOT NULL,
    proposed_setup  JSONB NOT NULL,
    result_json     JSONB NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_whatif_scenario ON what_if_results (scenario_id);

CREATE TABLE IF NOT EXISTS race_strategy_results (
    id           BIGSERIAL PRIMARY KEY,
    strategy_id  TEXT NOT NULL,
    circuit_id   TEXT NOT NULL,
    result_json  JSONB NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_strategy_circuit ON race_strategy_results (circuit_id);
"""


async def init_db() -> None:
    ddl = _DDL_PG if not _is_sqlite else _DDL
    async with engine.begin() as conn:
        for stmt in ddl.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                await conn.execute(text(stmt))
    logger.info("Digital Twin DB ready (%s)", "sqlite" if _is_sqlite else "postgres")


async def save_simulation_result(scenario_id: str, result: dict) -> None:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("""
                INSERT INTO simulation_results (scenario_id, result_json, created_at)
                VALUES (:scenario_id, :result_json, :created_at)
            """),
            {"scenario_id": scenario_id, "result_json": json.dumps(result), "created_at": ts},
        )
        await db.commit()


async def load_recent_simulations(limit: int = 50) -> list[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT DISTINCT ON (scenario_id) scenario_id, result_json, created_at
                FROM simulation_results
                ORDER BY scenario_id, created_at DESC
                LIMIT :limit
            """) if not _is_sqlite else text("""
                SELECT scenario_id, result_json, created_at
                FROM simulation_results
                GROUP BY scenario_id
                HAVING created_at = MAX(created_at)
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
        rows = result.fetchall()
    return [json.loads(r.result_json) for r in rows]


async def save_what_if_result(
    scenario_id: str,
    circuit_id: str,
    session_id: str,
    baseline_setup: str,
    proposed_setup: dict,
    result: dict,
) -> None:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("""
                INSERT INTO what_if_results
                    (scenario_id, circuit_id, session_id, baseline_setup, proposed_setup, result_json, created_at)
                VALUES
                    (:scenario_id, :circuit_id, :session_id, :baseline_setup, :proposed_setup, :result_json, :created_at)
            """),
            {
                "scenario_id": scenario_id,
                "circuit_id": circuit_id,
                "session_id": session_id,
                "baseline_setup": baseline_setup,
                "proposed_setup": json.dumps(proposed_setup),
                "result_json": json.dumps(result),
                "created_at": ts,
            },
        )
        await db.commit()


async def save_race_strategy(strategy_id: str, circuit_id: str, result: dict) -> None:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("""
                INSERT INTO race_strategy_results (strategy_id, circuit_id, result_json, created_at)
                VALUES (:strategy_id, :circuit_id, :result_json, :created_at)
            """),
            {"strategy_id": strategy_id, "circuit_id": circuit_id, "result_json": json.dumps(result), "created_at": ts},
        )
        await db.commit()


async def load_race_strategies(circuit_id: str | None = None, limit: int = 20) -> list[dict]:
    async with AsyncSessionLocal() as db:
        if circuit_id:
            result = await db.execute(
                text("SELECT result_json FROM race_strategy_results WHERE circuit_id = :cid ORDER BY created_at DESC LIMIT :limit"),
                {"cid": circuit_id, "limit": limit},
            )
        else:
            result = await db.execute(
                text("SELECT result_json FROM race_strategy_results ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit},
            )
        rows = result.fetchall()
    return [json.loads(r.result_json) for r in rows]


async def load_what_if_results(scenario_id: str | None = None, limit: int = 20) -> list[dict]:
    async with AsyncSessionLocal() as db:
        if scenario_id:
            result = await db.execute(
                text("SELECT result_json FROM what_if_results WHERE scenario_id = :sid ORDER BY created_at DESC LIMIT :limit"),
                {"sid": scenario_id, "limit": limit},
            )
        else:
            result = await db.execute(
                text("SELECT result_json FROM what_if_results ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit},
            )
        rows = result.fetchall()
    return [json.loads(r.result_json) for r in rows]
