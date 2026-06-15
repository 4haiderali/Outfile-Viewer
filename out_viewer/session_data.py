"""Session-state helpers shared by every tab module.

These were previously free functions defined directly in app.py. Moving
them here keeps app.py focused on page orchestration, and lets every tab
module read/write per-table edits, comparisons, and global search using the
same conventions instead of re-implementing them.

Convention: every per-table session key is namespaced by the *full
filename* the file was uploaded as (``current_name``), never by the file
stem. Two earlier tabs (Distribution and Insights in v25) used the stem
instead, which silently looked up a different session key than the one
Derived Columns wrote to -- so derived columns never showed up there. Keep
using ``current_name`` everywhere.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from .columns import main_table
from .parser import parse_output


@st.cache_data(show_spinner="Parsing file…", max_entries=12)
def cached_parse(file_bytes: bytes) -> dict:
    text = file_bytes.decode("utf-8", errors="replace")
    if not text.strip():
        raise ValueError("The uploaded file is empty.")
    if text.count("\x00") > max(10, len(text) // 1000):
        raise ValueError("The uploaded file looks binary, not text.")
    return parse_output(text)


def derived_key(file_label: str, table_name: str) -> str:
    return f"derived_{file_label}_{table_name}"


def get_session_table(table, file_label: str) -> pd.DataFrame:
    key = derived_key(file_label, table.name)
    if key in st.session_state:
        return st.session_state[key].copy()
    return table.data.copy()


def set_session_table(table, file_label: str, df: pd.DataFrame) -> None:
    st.session_state[derived_key(file_label, table.name)] = df.copy()


def register_raw_file(name: str, file_bytes: bytes) -> None:
    parsed = cached_parse(file_bytes)
    st.session_state.setdefault("file_history", {})
    st.session_state["file_history"][name] = {
        "name": name,
        "bytes": file_bytes,
        "parsed": parsed,
        "size": len(file_bytes),
    }


def register_file(uploaded_file) -> None:
    register_raw_file(uploaded_file.name, uploaded_file.getvalue())


def comparison_files_with_primary_tables() -> list[str]:
    history = st.session_state.get("file_history", {})
    out = []
    for name, record in history.items():
        if main_table(record["parsed"]["tables"]) is not None:
            out.append(name)
    return out


def build_comparison(base_name, compare_name, column, index_column=None):
    history = st.session_state["file_history"]
    base_table = main_table(history[base_name]["parsed"]["tables"])
    compare_table = main_table(history[compare_name]["parsed"]["tables"])
    base_df = get_session_table(base_table, base_name)
    compare_df = get_session_table(compare_table, compare_name)

    if index_column and index_column in base_df.columns and index_column in compare_df.columns:
        left = base_df[[index_column, column]].rename(columns={column: f"{base_name} {column}"})
        right = compare_df[[index_column, column]].rename(columns={column: f"{compare_name} {column}"})
        merged = left.merge(right, on=index_column, how="inner")
        x_col = index_column
    else:
        left = base_df[[column]].reset_index().rename(columns={"index": "Row", column: f"{base_name} {column}"})
        right = compare_df[[column]].reset_index().rename(columns={"index": "Row", column: f"{compare_name} {column}"})
        merged = left.merge(right, on="Row", how="inner")
        x_col = "Row"

    base_col = f"{base_name} {column}"
    compare_col = f"{compare_name} {column}"
    merged["Delta"] = pd.to_numeric(merged[compare_col], errors="coerce") - pd.to_numeric(merged[base_col], errors="coerce")
    denominator = pd.to_numeric(merged[base_col], errors="coerce").replace(0, np.nan)
    merged["Delta %"] = (merged["Delta"] / denominator * 100).round(4)
    return merged, x_col, base_col, compare_col


def all_violation_rows(df: pd.DataFrame, rules) -> pd.DataFrame:
    from .rules import violating_rows

    frames = []
    for rule in rules:
        out = violating_rows(df, rule)
        if not out.empty:
            frames.append(out)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def global_search_tables(tables, file_label: str, query: str) -> pd.DataFrame:
    query = query.strip()
    if not query:
        return pd.DataFrame()

    rows = []

    for table_index, table in enumerate(tables, start=1):
        df = get_session_table(table, file_label)
        if df.empty:
            continue

        string_df = df.astype(str)
        match_df = string_df.apply(
            lambda col: col.str.contains(query, case=False, na=False, regex=False)
        )
        row_mask = match_df.any(axis=1)

        for row_index in match_df.index[row_mask]:
            matched_columns = list(match_df.columns[match_df.loc[row_index]])
            row = string_df.loc[row_index]
            rows.append(
                {
                    "Table #": table_index,
                    "Table Name": table.name,
                    "Kind": table.kind,
                    "Row Index": row_index,
                    "Matched Columns": ", ".join(map(str, matched_columns)),
                    "Row Preview": " | ".join(str(row[col]) for col in string_df.columns[:8]),
                }
            )

    return pd.DataFrame(rows)
