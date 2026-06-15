"""Derived & Units tab: formula calculator (with templates) and column unit
tagging. These were two separate top-level tabs in v25, but they're both
"prepare your columns before analysis" steps, so they share one tab here.
"""

from __future__ import annotations

import streamlit as st

from ..cockpit import formula_templates
from ..columns import numeric_columns, table_options
from ..derived import evaluate_formula, sanitized_column_map
from ..session_data import derived_key, get_session_table, set_session_table
from ..ui_helpers import build_download_button, copy_tsv_button, dataframe_view
from ..units import default_unit_map, unit_table


def render(ctx) -> None:
    sub_derived, sub_units = st.tabs(["Derived Columns", "Units"])

    with sub_derived:
        _render_derived(ctx)

    with sub_units:
        _render_units(ctx)


def _render_derived(ctx) -> None:
    st.subheader("Derived Column Calculator")
    derived_tables = table_options(ctx.tables, require_numeric_cols=1)
    if not derived_tables:
        st.info("No numeric tables available for derived columns.")
        return

    names = [
        f"{i + 1}. {t.name} [{t.kind}] — "
        f"{len(get_session_table(t, ctx.current_name))} rows × {len(get_session_table(t, ctx.current_name).columns)} columns"
        for i, t in enumerate(derived_tables)
    ]
    selected = st.selectbox("Table", names, key="derived_table_select")
    table = derived_tables[names.index(selected)]
    df = get_session_table(table, ctx.current_name)

    st.markdown("**Column names available in formulas**")
    dataframe_view(sanitized_column_map(df))

    history_key = f"formula_history_{ctx.current_name}_{table.name}"
    st.session_state.setdefault(history_key, [])
    nums = numeric_columns(df)
    example = f"{nums[0]}_pct = {nums[0]} * 100" if nums else "NewColumn = 1"
    if len(nums) >= 2:
        example = f"{nums[0]}_plus_{nums[1]} = {nums[0]} + {nums[1]}"

    picked_history = (
        st.selectbox("Formula history", [""] + st.session_state[history_key], key="formula_history")
        if st.session_state[history_key] else None
    )
    formula = st.text_input("Formula", value=picked_history or example, placeholder="NewColumn = Ia + Ib")
    st.caption("Allowed operators: +, -, *, /, **, %. Allowed functions: abs, sqrt, log, log10, exp, min, max, round.")

    c1, c2 = st.columns(2)
    if c1.button("Add derived column"):
        try:
            new_df, new_col = evaluate_formula(df, formula)
            set_session_table(table, ctx.current_name, new_df)
            if formula not in st.session_state[history_key]:
                st.session_state[history_key].insert(0, formula)
                st.session_state[history_key] = st.session_state[history_key][:10]
            st.success(f"Added derived column: {new_col}")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add derived column: {exc}")
    if c2.button("Reset derived columns for this table"):
        key = derived_key(ctx.current_name, table.name)
        if key in st.session_state:
            del st.session_state[key]
        st.rerun()

    st.subheader("Current Table with Derived Columns")
    dataframe_view(df)
    copy_tsv_button(df, "Download table with derived columns as TSV")
    build_download_button("Download table with derived columns as CSV", df, f"{ctx.stem}_derived_columns.csv")

    st.markdown("#### Formula Templates")
    st.caption("Ready-made formulas for common derived quantities based on this table's numeric columns.")
    templates = formula_templates(numeric_columns(df))
    if templates.empty:
        st.info("Not enough numeric columns to suggest formula templates.")
    else:
        dataframe_view(templates)


def _render_units(ctx) -> None:
    st.subheader("Column Units")
    if ctx.primary_table is None:
        st.info("No primary numeric table was detected, so there are no units to tag yet.")
        return

    df = get_session_table(ctx.primary_table, ctx.current_name)
    nums = numeric_columns(df)
    if not nums:
        st.info("The primary table has no numeric columns.")
        return

    st.write("Tag units once, then statistics and reports will carry the unit labels.")
    editable_units = unit_table(nums, ctx.unit_map)
    edited_units = st.data_editor(
        editable_units,
        hide_index=True,
        num_rows="fixed",
        width="stretch",
        key=f"unit_editor_{ctx.current_name}",
    )
    c1, c2 = st.columns(2)
    if c1.button("Save unit tags"):
        st.session_state[ctx.unit_key] = {
            str(row["Column"]): str(row.get("Unit", "") or "")
            for _, row in edited_units.iterrows()
        }
        st.success("Saved unit tags for this file.")
        st.rerun()
    if c2.button("Reset inferred units"):
        st.session_state[ctx.unit_key] = default_unit_map(nums)
        st.rerun()
    build_download_button("Download unit tags as CSV", unit_table(nums, st.session_state[ctx.unit_key]), f"{ctx.stem}_column_units.csv")
