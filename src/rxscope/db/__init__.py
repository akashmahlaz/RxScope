"""Database connection pool management."""

from __future__ import annotations

from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

from rxscope.config import settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool (lazy singleton)."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=2,
            max_size=settings.database_pool_size,
            open=True,
        )
    return _pool


@contextmanager
def get_connection():
    """Yield a connection from the pool."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def close_pool():
    """Shut down the pool cleanly."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def run_schema():
    """Apply the schema.sql to the database."""
    import importlib.resources as pkg_resources
    from pathlib import Path

    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        conn.execute(sql)
        conn.commit()
