"""Raw & Diagnostics tab: raw text browsing/search and parser diagnostics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..ui_helpers import dataframe_view


def render(ctx) -> None:
    sub_raw, sub_diag = st.tabs(["Raw Text", "Parse Diagnostics"])

    with sub_raw:
        _render_raw(ctx)

    with sub_diag:
        _render_diagnostics(ctx)


def _render_raw(ctx) -> None:
    st.subheader("Raw")
    lines = ctx.parsed["lines"]
    raw_query = st.text_input("Find text in raw file", key="raw_query")
    if raw_query:
        matches = [{"Line": i + 1, "Text": line} for i, line in enumerate(lines) if raw_query.lower() in line.lower()]
        st.metric("Matches", len(matches))
        dataframe_view(pd.DataFrame(matches))
    else:
        page_size = st.selectbox("Lines per page", [250, 500, 1000, 2000], index=1, key="raw_page_size")
        total_pages = max(1, (len(lines) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="raw_page")
        start = (page - 1) * page_size
        end = min(start + page_size, len(lines))
        st.caption(f"Showing lines {start + 1:,}–{end:,} of {len(lines):,}")
        st.text("\n".join(lines[start:end]))


def _render_diagnostics(ctx) -> None:
    st.subheader("Parse Diagnostics")
    diagnostics = ctx.diagnostics
    diag_rows = [
        {"Item": "Main tables detected", "Value": diagnostics.get("main_tables_detected", 0)},
        {"Item": "Probability tables detected", "Value": diagnostics.get("probability_tables_detected", 0)},
        {"Item": "Metric rows detected", "Value": diagnostics.get("metric_rows_detected", 0)},
        {"Item": "Lines processed", "Value": diagnostics.get("lines_processed", len(ctx.parsed["lines"]))},
        {"Item": "Cached parser active", "Value": "Yes"},
    ]
    dataframe_view(pd.DataFrame(diag_rows))
    warnings = diagnostics.get("warnings", [])
    if warnings:
        st.warning("Parser warnings were generated.")
        dataframe_view(pd.DataFrame({"Warning": warnings}))
    else:
        st.success("No parser warnings.")
