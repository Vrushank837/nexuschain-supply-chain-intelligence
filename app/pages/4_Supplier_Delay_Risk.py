import pandas as pd
import streamlit as st

from analytics.data_access import read_query
from app.common import db_error, header, setup_page
from services.prediction_service import delay_prediction, explain_delay, load_delay_model

setup_page("Supplier delay risk", "⚠️")
header(
    "Supplier delay risk",
    "Predict shipment delay probability using historical supplier and order signals",
)
try:
    po = read_query(
        "SELECT po_id, order_date, supplier_id, part_id, quantity, unit_price FROM purchase_orders WHERE status='open' ORDER BY order_date DESC LIMIT 200"
    )
    parts = read_query("SELECT part_id, category, lead_time_days FROM parts")
    suppliers = read_query("SELECT supplier_id, supplier_name FROM suppliers")
    df = po.merge(parts, on="part_id").merge(suppliers, on="supplier_id")
    if df.empty:
        st.info("No open orders available.")
    else:
        idx = st.selectbox(
            "Open order",
            df.index,
            format_func=lambda i: f"{df.loc[i,'po_id']} · {df.loc[i,'supplier_name']} · {df.loc[i,'part_id']}",
        )
        row = df.loc[[idx]].copy()
        # Build supplier history using only orders placed before the selected order.
        hist = read_query(
            """
            SELECT
                po.supplier_id,
                po.po_id,
                COALESCE((
                    SELECT AVG(CASE WHEN h.actual_delivery_date > h.promised_date THEN 1.0 ELSE 0.0 END)
                    FROM purchase_orders h
                    WHERE h.supplier_id = po.supplier_id
                      AND h.status = 'delivered'
                      AND h.actual_delivery_date IS NOT NULL
                      AND h.order_date < po.order_date
                ), 0) AS supplier_prior_delay_rate,
                COALESCE((
                    SELECT AVG(GREATEST(0, h.actual_delivery_date - h.promised_date))
                    FROM purchase_orders h
                    WHERE h.supplier_id = po.supplier_id
                      AND h.status = 'delivered'
                      AND h.actual_delivery_date IS NOT NULL
                      AND h.order_date < po.order_date
                ), 0) AS supplier_prior_avg_delay,
                (
                    SELECT COUNT(*)
                    FROM purchase_orders h
                    WHERE h.supplier_id = po.supplier_id
                      AND h.status = 'delivered'
                      AND h.actual_delivery_date IS NOT NULL
                      AND h.order_date < po.order_date
                ) AS supplier_prior_orders
            FROM purchase_orders po
            WHERE po.po_id = :po_id
        """,
            {"po_id": row.iloc[0]["po_id"]},
        )
        row = row.merge(hist.drop(columns=["po_id"]), on="supplier_id", how="left")
        row["order_date"] = pd.to_datetime(row.order_date)
        row["month"] = row.order_date.dt.month
        row["day_of_week"] = row.order_date.dt.dayofweek
        row["supplier_prior_delay_rate"] = row.supplier_prior_delay_rate.fillna(0)
        row["supplier_prior_avg_delay"] = row.supplier_prior_avg_delay.fillna(0)
        row["supplier_prior_orders"] = row.supplier_prior_orders.fillna(0)
        features = row[
            [
                "supplier_id",
                "part_id",
                "category",
                "lead_time_days",
                "quantity",
                "unit_price",
                "month",
                "day_of_week",
                "supplier_prior_delay_rate",
                "supplier_prior_avg_delay",
                "supplier_prior_orders",
            ]
        ]
        model = load_delay_model()
        probability = delay_prediction(model, features)
        st.metric("Predicted delay probability", f"{probability:.1%}")
        st.progress(min(probability, 1.0))
        st.subheader("Why?")
        try:
            st.dataframe(explain_delay(features), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"SHAP explanation unavailable: {exc}")
except Exception as exc:
    db_error(exc)
