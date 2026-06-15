"""Compare tab: overlay two files' shared columns and inspect deltas, or
treat one file as a golden/baseline reference and get a pass/fail verdict.

v25 had these as two separate top-level tabs ("Compare" and "Baseline")
that both started with "pick two files with primary tables" -- here that's
one shared step, and a mode toggle switches the rest of the view.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from ..baseline import baseline_verdict, compare_to_baseline, likely_index_columns
from ..columns import main_table, numeric_columns
from ..constants import INDEX_NAMES
from ..export import source_stem
from ..session_data import build_comparison, comparison_files_with_primary_tables, get_session_table
from ..ui_helpers import build_download_button, dataframe_view, plotly_view, styled_dataframe_view


def render(ctx) -> None:
    st.subheader("Compare Files")

    history_count = ctx.file_count
    compare_options = comparison_files_with_primary_tables()

    if history_count < 2:
        st.info("Upload at least two files to use Compare mode.")
        return
    if len(compare_options) < 2:
        st.info("At least two loaded files need primary numeric tables before they can be compared.")
        return

    mode = st.radio(
        "Comparison mode",
        ["Overlay & Delta", "Baseline Verdict (pass/fail)"],
        horizontal=True,
        key="compare_mode",
    )

    if mode == "Overlay & Delta":
        c1, c2 = st.columns(2)
        base_name = c1.selectbox("Base file", compare_options, key="cmp_base")
        compare_name = c2.selectbox("Compare file", compare_options, key="cmp_compare")
        if base_name == compare_name:
            st.info("Choose two different files to compare.")
            return
        _render_overlay(base_name, compare_name)
    else:
        c1, c2 = st.columns(2)
        base_name = c1.selectbox("Golden / baseline file", compare_options, key="baseline_base")
        candidate_name = c2.selectbox("Candidate file", compare_options, key="baseline_candidate")
        if base_name == candidate_name:
            st.info("Choose two different files.")
            return
        _render_baseline(base_name, candidate_name)


def _render_overlay(base_name: str, compare_name: str) -> None:
    base_table = main_table(st.session_state["file_history"][base_name]["parsed"]["tables"])
    compare_table = main_table(st.session_state["file_history"][compare_name]["parsed"]["tables"])
    base_df = get_session_table(base_table, base_name)
    compare_df = get_session_table(compare_table, compare_name)
    shared_numeric = [c for c in numeric_columns(base_df) if c in numeric_columns(compare_df)]

    if not shared_numeric:
        st.warning("No shared numeric columns found.")
        return

    value_col = st.selectbox("Column to compare", shared_numeric, key="cmp_col")
    possible_index = [c for c in shared_numeric if str(c).lower() in INDEX_NAMES]
    index_col = st.selectbox("Match rows by", ["Row order"] + possible_index, key="cmp_index")

    merged, x_col, base_col, compare_col = build_comparison(
        base_name, compare_name, value_col, None if index_col == "Row order" else index_col,
    )
    st.metric("Matched rows", len(merged))
    dataframe_view(merged)
    build_download_button(
        "Download comparison delta as CSV", merged,
        f"comparison_{source_stem(base_name)}_vs_{source_stem(compare_name)}_{value_col}.csv",
    )

    long = merged[[x_col, base_col, compare_col]].melt(id_vars=[x_col], var_name="File", value_name=value_col)
    plotly_view(px.line(long, x=x_col, y=value_col, color="File", markers=True, title=f"{value_col}: {base_name} vs {compare_name}"))
    plotly_view(px.line(merged, x=x_col, y="Delta", markers=True, title=f"Delta: {compare_name} - {base_name}"))


def _render_baseline(base_name: str, candidate_name: str) -> None:
    base_table = main_table(st.session_state["file_history"][base_name]["parsed"]["tables"])
    candidate_table = main_table(st.session_state["file_history"][candidate_name]["parsed"]["tables"])
    base_df = get_session_table(base_table, base_name)
    candidate_df = get_session_table(candidate_table, candidate_name)

    common_index_cols = [c for c in likely_index_columns(base_df) if c in likely_index_columns(candidate_df)]
    index_col = st.selectbox("Match rows by", ["Row order"] + common_index_cols, key="baseline_index")
    abs_threshold = st.number_input("Optional max absolute delta threshold", value=0.0, min_value=0.0, step=0.1)
    pct_threshold = st.number_input("Optional max percent delta threshold", value=0.0, min_value=0.0, step=0.1)

    summary, deltas = compare_to_baseline(
        base_name, candidate_name, base_df, candidate_df,
        index_col=None if index_col == "Row order" else index_col,
    )

    if summary.empty:
        st.warning("No shared numeric analysis columns were found.")
        return

    verdict = baseline_verdict(
        summary,
        abs_threshold=abs_threshold if abs_threshold > 0 else None,
        pct_threshold=pct_threshold if pct_threshold > 0 else None,
    )
    st.markdown("#### Baseline Verdict")
    styled_dataframe_view(verdict, preset="compliance")
    build_download_button("Download baseline verdict", verdict, f"{source_stem(base_name)}_vs_{source_stem(candidate_name)}_baseline_verdict.csv")

    st.markdown("#### Row-Level Deltas")
    dataframe_view(deltas)
    build_download_button("Download row-level deltas", deltas, f"{source_stem(base_name)}_vs_{source_stem(candidate_name)}_row_deltas.csv")

    top_col = summary.iloc[0]["Column"]
    if f"{top_col} Δ" in deltas.columns:
        x_col = "Row" if "Row" in deltas.columns else deltas.columns[0]
        fig = px.line(deltas, x=x_col, y=f"{top_col} Δ", markers=True, title=f"Largest Delta Column: {top_col}")
        plotly_view(fig)
