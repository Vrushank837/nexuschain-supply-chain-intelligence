"""SQL-backed data access functions used by the dashboard and services."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from utils.config import settings

ROOT = Path(__file__).resolve().parent.parent


def engine():
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def read_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def kpis() -> pd.DataFrame:
    return read_query((ROOT / "database/queries/kpis.sql").read_text(encoding="utf-8"))


def supplier_performance() -> pd.DataFrame:
    return read_query("SELECT * FROM supplier_performance ORDER BY on_time_rate_pct DESC, total_orders DESC")


def supplier_monthly() -> pd.DataFrame:
    return read_query("SELECT * FROM monthly_supplier_delivery ORDER BY month")


def inventory_summary() -> pd.DataFrame:
    return read_query("SELECT * FROM inventory_summary ORDER BY stockout_days DESC, safety_stock_days DESC")


def bom_tree(root_part_id: str) -> pd.DataFrame:
    sql = (ROOT / "database/queries/bom_recursive.sql").read_text(encoding="utf-8")
    return read_query(sql, {"root_part_id": root_part_id})


def parts() -> pd.DataFrame:
    return read_query("SELECT * FROM parts ORDER BY part_id")


def high_risk_suppliers(limit: int = 10) -> pd.DataFrame:
    return read_query("SELECT * FROM supplier_performance ORDER BY on_time_rate_pct ASC LIMIT :limit", {"limit": limit})
