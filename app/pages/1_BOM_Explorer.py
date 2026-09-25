import plotly.express as px
import streamlit as st

from analytics.data_access import bom_tree, parts
from app.common import db_error, header, setup_page

setup_page("BOM explorer", "🌳")
header("BOM explorer", "Trace multi-level product dependencies and cumulative cost")
try:
    p = parts()
    options = p[p.part_type.isin(["finished_good", "assembly", "subassembly"])].part_id.tolist()
    root: str = st.selectbox("Root product / assembly", options)
    tree = bom_tree(root)
    if tree.empty:
        st.info("No BOM relationships found for this root.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Components", len(tree))
        c2.metric("Max depth", int(tree.level.max()))
        c3.metric("Roll-up cost", f"€{tree.cumulative_cost.sum():,.2f}")
        st.dataframe(tree, use_container_width=True, hide_index=True)
        st.subheader("Dependency graph")
        nodes = set(tree["part_id"].tolist())
        labels = dict(zip(tree.part_id, tree.part_name, strict=False))
        lines = ["digraph BOM {", "rankdir=LR;"]
        for node in nodes:
            safe_label = str(labels.get(node, node)).replace('"', "'")
            lines.append(f'"{node}" [label="{safe_label}"];')
        for _, row in tree.iterrows():
            parent = (
                row["dependency_path"].split(" -> ")[-2]
                if " -> " in row["dependency_path"]
                else root
            )
            lines.append(f'"{parent}" -> "{row.part_id}";')
        lines.append("}")
        st.graphviz_chart("\n".join(lines), use_container_width=True)
        fig = px.sunburst(
            tree,
            path=["part_type", "category", "part_name"],
            values="cumulative_cost",
            title="Cumulative cost composition",
        )
        st.plotly_chart(fig, use_container_width=True)
except Exception as exc:
    db_error(exc)
