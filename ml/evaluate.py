"""Reusable model evaluation helpers."""

from __future__ import annotations

import json
from pathlib import Path

from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_binary(y_true, probabilities, threshold: float = 0.5) -> dict:
    pred = (probabilities >= threshold).astype(int)
    result = {
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)) if len(set(y_true)) > 1 else 0.0,
        "pr_auc": (
            float(average_precision_score(y_true, probabilities)) if len(set(y_true)) > 1 else 0.0
        ),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
        "classification_report": classification_report(
            y_true, pred, zero_division=0, output_dict=True
        ),
    }
    return result


def save_metrics(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, default=float), encoding="utf-8")
