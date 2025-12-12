"""Shared configuration helpers for backend services."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2
from psycopg2.pool import SimpleConnectionPool

DEFAULT_INDEX_PATH = (Path(__file__).resolve().parent.parent / "index" / "reviews.index").resolve()
REQUIRED_ENV_VARS = ("PG_NAME", "PG_USER", "PG_PASSWORD", "PG_HOST")


def ensure_env_loaded() -> None:
    """Load environment variables and validate required keys are present."""

    load_dotenv()
    missing = [key for key in REQUIRED_ENV_VARS if key not in os.environ]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")


def resolve_index_path() -> Path:
    """Resolve the FAISS index path, honoring an override if provided."""

    override = os.environ.get("FAISS_INDEX_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_INDEX_PATH


def create_pg_connection():
    """Create a PostgreSQL connection using validated environment variables."""

    ensure_env_loaded()
    return psycopg2.connect(
        dbname=os.environ["PG_NAME"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432),
    )


def create_connection_pool(minconn: int = 1, maxconn: int = 5) -> SimpleConnectionPool:
    """Create a simple PostgreSQL connection pool for web services."""

    ensure_env_loaded()
    return SimpleConnectionPool(
        minconn,
        maxconn,
        dbname=os.environ["PG_NAME"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432),
    )
