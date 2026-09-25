"""Train leakage-safe supplier delay classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from ml.evaluate import evaluate_binary, save_metrics
from ml.features import supplier_delay_features
from utils.config import settings
from utils.logging_config import get_logger

log = get_logger(__name__)
CAT = ["supplier_id", "part_id", "category"]
NUM = [
    "lead_time_days",
    "quantity",
    "unit_price",
    "month",
    "day_of_week",
    "supplier_prior_delay_rate",
    "supplier_prior_avg_delay",
    "supplier_prior_orders",
]


def build_pipeline(model):
    prep = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                NUM,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CAT,
            ),
        ]
    )
    return Pipeline([("preprocessor", prep), ("model", model)])


def train(output_dir: Path = settings.model_dir) -> dict:
    df = supplier_delay_features()
    cutoff = df["order_date"].quantile(0.8)
    train_df, test_df = df[df.order_date <= cutoff], df[df.order_date > cutoff]
    X_train, y_train = train_df[CAT + NUM], train_df.delay_flag
    X_test, y_test = test_df[CAT + NUM], test_df.delay_flag
    neg, pos = max(1, int((y_train == 0).sum())), max(1, int((y_train == 1).sum()))
    scale_pos_weight = neg / pos

    baseline = build_pipeline(LogisticRegression(max_iter=1000, class_weight="balanced"))
    baseline.fit(X_train, y_train)
    base_metrics = evaluate_binary(y_test, baseline.predict_proba(X_test)[:, 1])

    model = build_pipeline(
        XGBClassifier(
            n_estimators=350,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=settings.random_seed,
            scale_pos_weight=scale_pos_weight,
            n_jobs=2,
        )
    )
    model.fit(X_train, y_train)
    metrics = evaluate_binary(y_test, model.predict_proba(X_test)[:, 1])
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / settings.delay_model_name)
    save_metrics(
        {
            "task": "supplier_delay",
            "cutoff": str(cutoff.date()),
            "baseline": base_metrics,
            "xgboost": metrics,
        },
        output_dir / "supplier_delay_metrics.json",
    )
    (output_dir / "supplier_delay_metadata.json").write_text(
        json.dumps(
            {
                "categorical_features": CAT,
                "numeric_features": NUM,
                "target": "delay_flag",
                "cutoff": str(cutoff.date()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info("delay_model_trained", roc_auc=metrics["roc_auc"], f1=metrics["f1"])
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=settings.model_dir)
    args = parser.parse_args()
    train(args.output)
