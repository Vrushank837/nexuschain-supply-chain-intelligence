"""Create schema and load generated CSV files into PostgreSQL."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from utils.config import settings
from utils.logging_config import get_logger

log = get_logger(__name__)
ORDER = ["suppliers", "parts", "bom", "purchase_orders", "inventory", "sales_orders"]


def create_schema(engine) -> None:
    schema = Path("database/schema.sql").read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in [s.strip() for s in schema.split(";") if s.strip()]:
            conn.execute(text(statement))
    views = Path("database/views.sql").read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in [s.strip() for s in views.split(";") if s.strip()]:
            conn.execute(text(statement))


def load(data_dir: Path, replace: bool = False) -> None:
    engine = create_engine(settings.database_url, future=True)
    create_schema(engine)
    if replace:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "TRUNCATE TABLE sales_orders, inventory, purchase_orders, bom, parts, suppliers RESTART IDENTITY CASCADE"
                )
            )
    for table in ORDER:
        df = pd.read_csv(data_dir / f"{table}.csv")
        if table in {"purchase_orders", "inventory", "sales_orders"}:
            for col in [c for c in df.columns if "date" in c]:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        if table == "inventory":
            # Preserve the database-generated surrogate key.
            pass
        df.to_sql(table, engine, if_exists="append", index=False, method="multi", chunksize=2000)
        log.info("table_loaded", table=table, rows=len(df))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--replace", action="store_true", help="Replace existing table contents before loading."
    )
    args = parser.parse_args()
    load(args.input, replace=args.replace)
    log.info("database_load_complete")


if __name__ == "__main__":
    main()
