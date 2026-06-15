"""Compliance tab: threshold (min/max) rules and custom boolean-expression
rules, side by side on the same table -- previously two separate top-level
tabs ("Compliance" and "Expression Rules") that each required picking a
table independently and exported separate violation files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ..cockpit import compliance_templates
from ..columns import numeric_columns, table_options
from ..expression_rules import expression_rule_failures, expression_rule_summary
from ..rules import ThresholdRule, check_compliance, load_rules, save_rules
from ..session_data import all_violation_rows, get_session_table
from ..ui_helpers import build_download_button, copy_tsv_button, dataframe_view, styled_dataframe_view

RULES_FILE = Path("rules.json")


def render(ctx) -> None:
    compliance_tables = table_options(ctx.tables, require_numeric_cols=1)
    if not compliance_tables:
        st.info("No numeric tables available for compliance checks.")
        return

    names = [
        f"{i + 1}. {t.name} [{t.kind}] — "
        f"{len(get_session_table(t, ctx.current_name))} rows × {len(get_session_table(t, ctx.current_name).columns)} columns"
        for i, t in enumerate(compliance_tables)
    ]
    selected = st.selectbox("Compliance table", names, key="compliance_table_select")
    table = compliance_tables[names.index(selected)]
    df = get_session_table(table, ctx.current_name)
    nums = numeric_columns(df)

    sub_threshold, sub_expression, sub_templates = st.tabs(["Threshold Rules", "Custom Expression Rules", "Suggested Rules"])

    with sub_threshold:
        _render_threshold_rules(ctx, df, nums, selected)

    with sub_expression:
        _render_expression_rules(ctx, df)

    with sub_templates:
        _render_templates(nums)


def _render_threshold_rules(ctx, df: pd.DataFrame, nums: list[str], table_label: str) -> None:
    st.subheader("Threshold (Min/Max) Rules")
    session_key = f"rules_{ctx.current_name}_{table_label}"
    st.session_state.setdefault(session_key, [])
    st.write("Define pass/fail threshold rules for numeric columns. Rules can be saved to `rules.json` in the app folder.")

    with st.expander("Add threshold rule", expanded=not st.session_state[session_key]):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        rule_column = c1.selectbox("Column", nums, key="rule_col")
        direction_label = c2.selectbox("Rule type", ["Minimum allowed", "Maximum allowed"], key="rule_type")
        threshold = c3.number_input("Threshold", value=0.0, format="%.6f", key="rule_threshold")
        required_pct = c4.number_input("Required pass %", min_value=0.0, max_value=100.0, value=100.0, step=0.1, key="rule_req")
        default_name = f"{rule_column} {'>=' if direction_label == 'Minimum allowed' else '<='} {threshold:g}"
        rule_name = st.text_input("Rule name", value=default_name, key="rule_name")
        add_col, clear_col, save_col, load_col = st.columns(4)
        if add_col.button("Add rule"):
            direction = "min" if direction_label == "Minimum allowed" else "max"
            st.session_state[session_key].append(ThresholdRule(rule_name, rule_column, direction, float(threshold), float(required_pct)))
            st.rerun()
        if clear_col.button("Clear rules"):
            st.session_state[session_key] = []
            st.rerun()
        if save_col.button("Save rules"):
            save_rules(RULES_FILE, st.session_state[session_key])
            st.success(f"Saved rules to {RULES_FILE}")
        if load_col.button("Load rules"):
            st.session_state[session_key] = load_rules(RULES_FILE)
            st.rerun()

    rules = st.session_state[session_key]
    if not rules:
        st.info("No threshold rules defined yet.")
        return

    results = check_compliance(df, rules)
    styled_dataframe_view(results, preset="compliance")
    build_download_button("Download compliance results as CSV", results, f"{ctx.stem}_compliance_results.csv")
    failing = results[results["Status"].isin(["FAIL", "MISSING COLUMN", "NO DATA"])]
    if failing.empty:
        st.success("All threshold rules pass.")
    else:
        st.error(f"{len(failing)} threshold rule(s) failed or could not be evaluated.")

    violations = all_violation_rows(df, rules)
    st.subheader("Violating Rows")
    if violations.empty:
        st.success("No violating rows found.")
    else:
        dataframe_view(violations)
        copy_tsv_button(violations, "Download violating rows as TSV")
        build_download_button("Download violating rows as CSV", violations, f"{ctx.stem}_violating_rows.csv")


def _render_expression_rules(ctx, df: pd.DataFrame) -> None:
    st.subheader("Custom Expression Rules")
    st.caption("Examples: `Energy_max <= 60`, `(Ea > 0.95) & (Ea < 1.05)`, `abs(Current_A - Current_B) < 5`")

    expression = st.text_input("Boolean expression rule", key="expr_rule_input")
    rule_name = st.text_input("Rule name", value="Custom expression rule", key="expr_rule_name")
    if st.button("Save expression rule"):
        if expression.strip():
            st.session_state.setdefault("saved_expression_rules", [])
            st.session_state["saved_expression_rules"].append({"Name": rule_name, "Expression": expression})
            st.success("Expression rule saved.")
            st.rerun()
        else:
            st.warning("Enter an expression before saving.")

    saved_rules = st.session_state.get("saved_expression_rules", [])
    if saved_rules:
        with st.expander("Saved expression rules", expanded=False):
            saved_df = pd.DataFrame(saved_rules)
            dataframe_view(saved_df)
            selected_rule_names = [f"{idx + 1}. {r.get('Name', 'Rule')} — {r.get('Expression', '')}" for idx, r in enumerate(saved_rules)]
            selected_saved = st.selectbox("Load saved rule", [""] + selected_rule_names, key="load_saved_expr")
            if selected_saved:
                selected_index = selected_rule_names.index(selected_saved)
                expression = saved_rules[selected_index]["Expression"]
                st.info(f"Loaded expression: `{expression}`")

    if expression:
        try:
            summary = pd.DataFrame([expression_rule_summary(df, expression)])
            styled_dataframe_view(summary, preset="compliance")

            failures = expression_rule_failures(df, expression)
            st.metric("Failing rows", len(failures))
            if failures.empty:
                st.success("All rows pass this expression rule.")
            else:
                dataframe_view(failures)
                build_download_button("Download expression-rule failures", failures, f"{ctx.stem}_expression_rule_failures.csv")
        except Exception as exc:
            st.error(f"Expression rule error: {exc}")


def _render_templates(nums: list[str]) -> None:
    st.subheader("Suggested Threshold Rules")
    st.caption("Starting points based on this table's numeric columns -- copy the column/threshold into the Threshold Rules tab.")
    templates = compliance_templates(nums)
    if templates.empty:
        st.info("Not enough numeric columns to suggest compliance rule templates.")
    else:
        dataframe_view(templates)
