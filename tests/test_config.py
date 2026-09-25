"""Sanity tests for the configuration/logging bootstrap (Phase 1)."""

from utils.config import get_settings
from utils.logging_config import get_logger


def test_settings_load_with_defaults():
    settings = get_settings()
    assert settings.database_url.startswith("postgresql://")
    assert settings.random_seed == 42
    assert settings.n_suppliers > 0
    assert settings.n_parts > 0


def test_settings_is_cached_singleton():
    a = get_settings()
    b = get_settings()
    assert a is b


def test_model_paths_are_constructed_correctly():
    settings = get_settings()
    assert settings.delay_model_path.name == settings.delay_model_name
    assert settings.stockout_model_path.name == settings.stockout_model_name
    assert settings.delay_model_path.parent == settings.model_dir


def test_logger_can_be_created_and_used():
    log = get_logger(__name__)
    # Should not raise
    log.info("test_log_event", phase=1)
