"""Filter & Search tab: quick text + range filtering, an AND/OR condition
builder, and a global search across every detected table for the current
file -- previously three separate top-level tabs.
"""

from __future__ import annotations

import streamlit as st

from ..analytics import apply_numeric_filters
from ..columns import numeric_columns, safe_float_range, table_options
from ..filter_builder import NUMERIC_OPERATORS, TEXT_OPERATORS, apply_conditions, condition_summary
from ..session_data import get_session_table, global_search_tables
from ..ui_helpers import build_download_button, copy_tsv_button, dataframe_view


def render(ctx) -> None:
    sub_quick, sub_advanced, sub_search = st.tabs(["Quick Filter", "Advanced Filter", "Search All Tables"])

    with sub_quick:
        _render_quick_filter(ctx)

    with sub_advanced:
        _render_advanced_filter(ctx)

    with sub_search:
        _render_search_all(ctx)


def _table_picker(ctx, tables, *, key: str, label: str = "Table"):
    names = [
        f"{i + 1}. {t.name} [{t.kind}] — "
        f"{len(get_session_table(t, ctx.current_name))} rows × {len(get_session_table(t, ctx.current_name).columns)} columns"
        for i, t in enumerate(tables)
    ]
    selected = st.selectbox(label, names, key=key)
    index = names.index(selected)
    table = tables[index]
    return index, table, get_session_table(table, ctx.current_name)


def _render_quick_filter(ctx) -> None:
    st.subheader("Search / Filter Any Table")
    filter_tables = table_options(ctx.tables)
    if not filter_tables:
        st.info("No tables available to filter.")
        return

    table_index, table, df = _table_picker(ctx, filter_tables, key="filter_table_select")
    filtered = df.copy()

    query = st.text_input("Search all columns", key="quick_filter_query")
    if query:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    ranges = {}
    with st.expander("Numeric range filters"):
        for column in numeric_columns(df):
            safe_range = safe_float_range(df[column])
            if safe_range is not None:
                ranges[column] = st.slider(column, min_value=safe_range[0], max_value=safe_range[1], value=safe_range, key=f"range_{column}")
    filtered = apply_numeric_filters(filtered, ranges)

    st.metric("Filtered rows", len(filtered))
    dataframe_view(filtered)
    copy_tsv_button(filtered, "Download filtered rows as TSV")
    build_download_button("Download filtered rows as CSV", filtered, f"{ctx.stem}_{table.kind}_table_{table_index + 1}_filtered_rows.csv")


def _render_advanced_filter(ctx) -> None:
    st.subheader("Advanced Filter Builder")
    advanced_tables = table_options(ctx.tables)
    if not advanced_tables:
        st.info("No tables available to filter.")
        return

    table_index, table, df = _table_picker(ctx, advanced_tables, key="advanced_filter_select")
    numeric_cols = numeric_columns(df)
    all_cols = list(df.columns)

    num_conditions = st.number_input("Number of conditions", min_value=1, max_value=8, value=2, step=1, key="adv_num_conditions")
    joiner = st.radio("Combine conditions with", ["AND", "OR"], horizontal=True, key="adv_joiner")
    conditions = []
    for idx in range(int(num_conditions)):
        c1, c2, c3 = st.columns([2, 1.4, 2])
        column = c1.selectbox("Column", all_cols, key=f"adv_col_{idx}")
        operators = NUMERIC_OPERATORS + TEXT_OPERATORS if column in numeric_cols else TEXT_OPERATORS + NUMERIC_OPERATORS
        operator = c2.selectbox("Operator", operators, key=f"adv_op_{idx}")
        value = c3.text_input("Value", key=f"adv_val_{idx}")
        conditions.append({"column": column, "operator": operator, "value": value})

    st.caption(condition_summary(conditions, joiner))
    filtered = apply_conditions(df, conditions, joiner)
    st.metric("Filtered rows", len(filtered))
    dataframe_view(filtered)
    copy_tsv_button(filtered, "Download advanced-filtered rows as TSV")
    build_download_button("Download advanced-filtered rows as CSV", filtered, f"{ctx.stem}_{table.kind}_table_{table_index + 1}_advanced_filter.csv")


def _render_search_all(ctx) -> None:
    st.subheader("Global Search Across All Tables")
    query = st.text_input("Search text", key="global_search_query")
    if not query:
        st.info("Enter text to search across every detected table.")
        return

    results = global_search_tables(ctx.tables, ctx.current_name, query)
    st.metric("Matching rows", len(results))
    if results.empty:
        st.info("No matches found.")
    else:
        dataframe_view(results)
        copy_tsv_button(results, "Download search results as TSV")
        build_download_button("Download global search results as CSV", results, f"{ctx.stem}_global_search.csv")
