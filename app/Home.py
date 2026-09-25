"""NexusChain executive dashboard."""
from __future__ import annotations

import streamlit as st
import plotly.express as px

from analytics.data_access import high_risk_suppliers, inventory_summary, kpis
from app.common import db_error, header, setup_page

setup_page("Executive dashboard", "📊")
header("Executive dashboard", "Europe network · live operational snapshot")

try:
    k = kpis().iloc[0]
    cols = st.columns(5)
    cols[0].metric("Suppliers", f"{int(k.supplier_count):,}")
    cols[1].metric("Parts", f"{int(k.part_count):,}")
    cols[2].metric("Inventory value", f"€{float(k.inventory_value or 0):,.0f}")
    cols[3].metric("On-time delivery", f"{float(k.on_time_rate or 0):.1f}%")
    cols[4].metric("Current stockouts", f"{int(k.current_stockout_parts or 0):,}")

    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Highest supplier risk")
        df = high_risk_suppliers(8)
        st.dataframe(df[["supplier_name", "country", "total_orders", "on_time_rate_pct", "avg_delay_days"]], use_container_width=True, hide_index=True)
    with right:
        st.subheader("Inventory risk")
        inv = inventory_summary().head(10)
        fig = px.bar(inv, x="part_name", y="stockout_days", title="Stockout days")
        fig.update_layout(height=340, margin=dict(l=10,r=10,t=50,b=10), xaxis_title=None, yaxis_title="Days")
        st.plotly_chart(fig, use_container_width=True)
except Exception as exc:
    db_error(exc)

st.caption("NexusChain · synthetic ERP environment · model snapshot and KPIs are generated from the project database.")
