import plotly.express as px
import streamlit as st

from analytics.data_access import inventory_summary
from app.common import db_error, header, setup_page

setup_page("Inventory intelligence", "📦")
header("Inventory intelligence", "Monitor stock cover, safety stock and demand pressure")
try:
    df = inventory_summary()
    if df.empty:
        st.info("No inventory data available.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Parts tracked", len(df))
        c2.metric("Parts with stockouts", int((df.stockout_days > 0).sum()))
        c3.metric("Safety-stock breaches", int((df.safety_stock_days > 0).sum()))
        top = df.head(15)
        fig = px.bar(
            top,
            x="part_name",
            y=["stockout_days", "safety_stock_days"],
            barmode="group",
            title="Inventory risk by part",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
except Exception as exc:
    db_error(exc)
