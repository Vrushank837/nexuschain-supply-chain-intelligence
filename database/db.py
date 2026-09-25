"""Database engine helpers."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from utils.config import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


@contextmanager
def connection() -> Iterator[Connection]:
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def run_sql_file(path: str) -> None:
    with open(path, encoding="utf-8") as file:
        sql = file.read()
    with connection() as conn:
        for statement in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(text(statement))
