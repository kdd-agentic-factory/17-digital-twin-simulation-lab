"""Test fixtures — initialise the SQLite database before integration tests."""
import asyncio
import os

import pytest

# Use in-memory SQLite for all tests so there are no file artifacts and no
# schema-drift issues between runs.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """Create all tables in the in-memory test DB before the test session starts."""
    # Reimport database after the env-var is set to pick up the in-memory URL.
    import importlib
    import digital_twin_lab.database as db_module
    importlib.reload(db_module)

    async def _init():
        await db_module.init_db()

    asyncio.get_event_loop().run_until_complete(_init())
