"""Model loading and prediction helpers for the dashboard."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from ml.explainability import explain_pipeline
from utils.config import settings


def load_delay_model():
    return joblib.load(settings.delay_model_path)


def load_stockout_model():
    return joblib.load(settings.stockout_model_path)


def delay_prediction(model, row: pd.DataFrame) -> float:
    return float(model.predict_proba(row)[:, 1][0])


def stockout_prediction(model, row: pd.DataFrame) -> float:
    return float(model.predict_proba(row)[:, 1][0])


def explain_delay(row: pd.DataFrame) -> pd.DataFrame:
    return explain_pipeline(settings.delay_model_path, row)


def explain_stockout(row: pd.DataFrame) -> pd.DataFrame:
    return explain_pipeline(settings.stockout_model_path, row)
