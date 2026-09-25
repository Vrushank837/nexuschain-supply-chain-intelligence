"""Bootstrap a fresh local or hosted PostgreSQL database and model artifacts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from ml.train_delay_model import train as train_delay
from ml.train_stockout_model import train as train_stockout
from scripts.load_database import load
from scripts.validate_data import validate
from utils.config import settings
from utils.logging_config import get_logger

log = get_logger(__name__)


def database_has_data(database_url: str) -> bool:
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            exists = conn.execute(text("SELECT to_regclass('public.suppliers')")).scalar()
            if exists is None:
                return False
            return int(conn.execute(text("SELECT COUNT(*) FROM suppliers")).scalar_one()) > 0
    except Exception:
        return False
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing populated database."
    )
    parser.add_argument("--skip-models", action="store_true", help="Skip model training.")
    args = parser.parse_args()

    data_dir = Path("data/raw")
    if database_has_data(settings.database_url) and not args.force:
        log.info("bootstrap_database_already_populated", action="skip_load")
    else:
        subprocess.run([sys.executable, "-m", "scripts.generate_data"], check=True)
        issues = validate(data_dir)
        if issues:
            raise SystemExit(
                "Generated data failed validation; see data/processed/validation_report.txt"
            )
        load(data_dir, replace=True)

    if not args.skip_models:
        train_delay(settings.model_dir)
        train_stockout(settings.model_dir)

    log.info("bootstrap_complete")


if __name__ == "__main__":
    main()
