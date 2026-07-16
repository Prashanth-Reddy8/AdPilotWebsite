"""Database metadata smoke test independent of PostgreSQL availability."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
from app.models import User  # noqa: F401 -- registers every entity through package import


@pytest.mark.asyncio
async def test_v1_schema_creates_all_expected_tables() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        table_names = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )
    await engine.dispose()
    assert {
        "users",
        "meta_accounts",
        "meta_connection_sessions",
        "campaigns",
        "ad_sets",
        "ads",
        "creatives",
        "daily_metrics",
        "alerts",
        "settings",
        "products",
        "notification_logs",
        "sync_runs",
    } <= table_names
