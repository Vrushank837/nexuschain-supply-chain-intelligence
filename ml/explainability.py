"""SHAP explanations for trained XGBoost pipelines."""

from __future__ import annotations

import joblib
import pandas as pd
import shap


def explain_pipeline(model_path, features: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    pipeline = joblib.load(model_path)
    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    transformed = preprocessor.transform(features)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    names = preprocessor.get_feature_names_out()
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(transformed)
    if isinstance(values, list):
        values = values[-1]
    frame = pd.DataFrame({"feature": names, "shap_value": values[0]})
    frame["abs_shap"] = frame.shap_value.abs()
    return frame.sort_values("abs_shap", ascending=False).head(top_n).reset_index(drop=True)
