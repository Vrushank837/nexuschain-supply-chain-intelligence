import pandas as pd
import streamlit as st

from analytics.data_access import read_query
from app.common import db_error, header, setup_page
from services.prediction_service import explain_stockout, load_stockout_model, stockout_prediction

setup_page("Stockout risk", "📉")
header(
    "Stockout risk",
    "Estimate the probability that a part will reach or fall below safety stock within 14 days",
)
try:
    inv = read_query(
        "SELECT i.*, p.category, p.safety_stock, p.lead_time_days FROM inventory i JOIN parts p ON p.part_id=i.part_id WHERE i.date=(SELECT MAX(date) FROM inventory)"
    )
    hist = read_query(
        "SELECT part_id, AVG(consumed_quantity) AS demand_avg_7d, STDDEV(consumed_quantity) AS demand_std_7d, AVG(received_quantity) AS receipt_avg_14d FROM inventory GROUP BY part_id"
    )
    if inv.empty:
        st.info("No current inventory snapshot available.")
    else:
        df = inv.merge(hist, on="part_id", how="left")
        df["demand_avg_7d"] = df.demand_avg_7d.fillna(df.consumed_quantity.median())
        df["demand_std_7d"] = df.demand_std_7d.fillna(0)
        df["receipt_avg_14d"] = df.receipt_avg_14d.fillna(df.received_quantity.median())
        df["days_of_cover"] = df.closing_stock / df.demand_avg_7d.clip(lower=1)
        df["safety_stock_gap"] = df.closing_stock - df.safety_stock
        df["month"] = pd.to_datetime(df.date).dt.month
        df["day_of_week"] = pd.to_datetime(df.date).dt.dayofweek
        idx: int = st.selectbox(
            "Part",
            df.index,
            format_func=lambda i: f"{df.loc[i,'part_id']} · {df.loc[i,'category']}",
        )
        row = df.loc[[idx]]
        features = row[
            [
                "part_id",
                "category",
                "closing_stock",
                "safety_stock",
                "lead_time_days",
                "demand_avg_7d",
                "demand_std_7d",
                "receipt_avg_14d",
                "days_of_cover",
                "safety_stock_gap",
                "month",
                "day_of_week",
            ]
        ]
        model = load_stockout_model()
        probability = stockout_prediction(model, features)
        st.metric("14-day stockout probability", f"{probability:.1%}")
        st.progress(min(probability, 1.0))
        st.subheader("Why?")
        try:
            st.dataframe(explain_stockout(features), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"SHAP explanation unavailable: {exc}")
        st.subheader("Current inventory context")
        st.dataframe(
            row[
                [
                    "part_id",
                    "closing_stock",
                    "safety_stock",
                    "lead_time_days",
                    "demand_avg_7d",
                    "days_of_cover",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
except Exception as exc:
    db_error(exc)
