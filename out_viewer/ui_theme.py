"""Streamlit theme helpers for the viewer UI."""

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1320px;
            padding-top: 1.15rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.32rem;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.25rem;
            overflow-x: auto;
            white-space: nowrap;
            scrollbar-width: thin;
        }
        button[data-baseweb="tab"] {
            padding: 0.35rem 0.55rem;
            font-size: 0.88rem;
        }
        button[data-baseweb="tab"] p {
            font-size: 0.88rem;
        }
        .cockpit-hero {
            padding: 1rem 1.15rem;
            border-radius: 14px;
            background: rgba(59, 130, 246, 0.10);
            border: 1px solid rgba(96, 165, 250, 0.26);
            margin: 0.75rem 0 1rem 0;
        }
        .cockpit-hero h2 {
            margin: 0 0 0.25rem 0;
            font-size: 1.35rem;
        }
        .cockpit-hero p {
            margin: 0;
            color: inherit;
            opacity: 0.86;
        }
        .soft-note {
            opacity: 0.78;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="cockpit-hero"><h2>{title}</h2><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
