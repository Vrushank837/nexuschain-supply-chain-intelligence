"""
Centralized application configuration.

All modules that need configuration (database URL, seeds, model paths, ...)
import `settings` from this module instead of calling os.getenv() directly.
This keeps configuration in one auditable place and gives us validation
and type hints for free via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings, populated from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql://scuser:scpass@localhost:5432/supply_chain",
        description="Full SQLAlchemy-compatible connection string.",
    )

    # --- Synthetic data generation ---
    random_seed: int = 42
    n_suppliers: int = 60
    n_parts: int = 600
    n_bom_relationships: int = 1200
    n_purchase_orders: int = 55_000
    n_inventory_records: int = 110_000
    n_sales_orders: int = 55_000

    # --- ML ---
    model_dir: Path = PROJECT_ROOT / "models"
    delay_model_name: str = "supplier_delay_xgb.joblib"
    stockout_model_name: str = "stockout_risk_xgb.joblib"

    # --- App ---
    log_level: str = "INFO"
    environment: str = "development"

    @property
    def delay_model_path(self) -> Path:
        return self.model_dir / self.delay_model_name

    @property
    def stockout_model_path(self) -> Path:
        return self.model_dir / self.stockout_model_name


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance (loaded once per process)."""
    try:
        import streamlit as st

        database_url = st.secrets.get("DATABASE_URL")
    except Exception:
        database_url = None

    if database_url:
        return Settings(database_url=database_url)

    return Settings()


settings = get_settings()
