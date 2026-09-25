"""Shared Streamlit UI helpers."""

from __future__ import annotations

import streamlit as st


def setup_page(title: str, icon: str = "📦") -> None:
    st.set_page_config(
        page_title=f"NexusChain | {title}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
    <style>
    [data-testid="stSidebar"] {background: #0d1628;}
    [data-testid="stSidebar"] * {color: #e9eef7;}
    .hero {padding: 0.2rem 0 1rem 0;}
    .eyebrow {font-size: .72rem; letter-spacing: .18em; text-transform: uppercase; color: #5f6f86; font-weight: 700;}
    .subtle {color: #64748b;}
    .risk-high {color:#b42318;font-weight:700;}
    .risk-med {color:#b54708;font-weight:700;}
    .risk-low {color:#067647;font-weight:700;}
    </style>
    """,
        unsafe_allow_html=True,
    )


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">NexusChain · Supply Intelligence</div><h1>{title}</h1><div class="subtle">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def db_error(exc: Exception) -> None:
    st.error(
        "The database is not available. Configure DATABASE_URL and initialize the database first."
    )
    with st.expander("Technical details"):
        st.code(str(exc))


def model_error(exc: Exception) -> None:
    st.error(
        "The prediction model is not available. Train/bootstrap the models before using this page."
    )
    with st.expander("Technical details"):
        st.code(str(exc))
