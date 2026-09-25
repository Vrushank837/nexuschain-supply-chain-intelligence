import plotly.express as px
import streamlit as st

from analytics.data_access import supplier_monthly, supplier_performance
from app.common import db_error, header, setup_page

setup_page("Supplier intelligence", "🏭")
header(
    "Supplier intelligence",
    "Compare supplier reliability, capacity signals and delivery consistency",
)
try:
    df = supplier_performance()
    region = st.selectbox("Region", ["All"] + sorted(df.region.dropna().unique().tolist()))
    if region != "All":
        df = df[df.region == region]
    left, right = st.columns([1.5, 1])
    with left:
        monthly = supplier_monthly()
        if not df.empty:
            selected = st.multiselect(
                "Suppliers", df.supplier_id.tolist(), default=df.head(5).supplier_id.tolist()
            )
            if selected:
                monthly = monthly[monthly.supplier_id.isin(selected)]
        fig = px.line(
            monthly,
            x="month",
            y="on_time_rate_pct",
            color="supplier_id",
            markers=True,
            title="On-time delivery trend",
        )
        fig.update_layout(yaxis_title="On-time %", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Supplier register")
        st.dataframe(
            df[
                ["supplier_name", "country", "total_orders", "on_time_rate_pct", "avg_delay_days"]
            ].head(12),
            use_container_width=True,
            hide_index=True,
        )
    st.subheader("Full supplier analytics")
    st.dataframe(df, use_container_width=True, hide_index=True)
except Exception as exc:
    db_error(exc)
