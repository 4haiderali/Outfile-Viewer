"""Data tab: detected summary, main tables, probability/PDF tables, and
manual table extraction -- everything about *what was parsed from the file*
lives here as sub-tabs, instead of four separate top-level tabs.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from ..columns import numeric_columns
from ..manual_table import parse_manual_table, preview_lines
from ..ui_helpers import build_download_button, copy_tsv_button, dataframe_view, plotly_view
from ..session_data import get_session_table


def render(ctx) -> None:
    sub_summary, sub_tables, sub_pdf, sub_manual = st.tabs(
        ["Summary", "Main Tables", "PDF Tables", "Manual Table"]
    )

    with sub_summary:
        _render_summary(ctx)

    with sub_tables:
        _render_main_tables(ctx)

    with sub_pdf:
        _render_pdf_tables(ctx)

    with sub_manual:
        _render_manual_table(ctx)


def _render_summary(ctx) -> None:
    st.subheader("Detected Summary")
    if ctx.metadata_df.empty:
        st.info("No summary text was detected. That is okay; this section is optional.")
    else:
        dataframe_view(ctx.metadata_df)

    if ctx.primary_table is not None:
        st.subheader("Primary Table Preview")
        st.caption("Automatically selected as the largest detected main numeric table.")
        dataframe_view(get_session_table(ctx.primary_table, ctx.current_name).head(30).copy())


def _render_main_tables(ctx) -> None:
    st.subheader("Detected Main Tables")
    if not ctx.main_table_list:
        st.info("No main numeric tables were detected for this file.")
        return

    names = [
        f"{i + 1}. {t.name} — line {t.header_line}, "
        f"{len(get_session_table(t, ctx.current_name))} rows × {len(get_session_table(t, ctx.current_name).columns)} columns"
        for i, t in enumerate(ctx.main_table_list)
    ]
    selected = st.selectbox("Table", names, key="main_table_select")
    table_index = names.index(selected)
    table = ctx.main_table_list[table_index]
    df = get_session_table(table, ctx.current_name)
    st.write(f"Columns: `{', '.join(df.columns)}`")
    dataframe_view(df)
    copy_tsv_button(df)
    build_download_button("Download selected table as CSV", df, f"{ctx.stem}_main_table_{table_index + 1}.csv")


def _render_pdf_tables(ctx) -> None:
    st.subheader("Probability Density Function Tables")
    if not ctx.pdf_table_list:
        st.info("No probability/PDF tables were detected for this file.")
        return

    names = [
        f"{i + 1}. {t.name} — line {t.header_line}, {len(t.data)} rows × {len(t.columns)} columns"
        for i, t in enumerate(ctx.pdf_table_list)
    ]
    selected = st.selectbox("Probability table", names, key="pdf_table_select")
    table_index = names.index(selected)
    table = ctx.pdf_table_list[table_index]
    df = get_session_table(table, ctx.current_name)
    dataframe_view(df)
    build_download_button("Download PDF table as CSV", df, f"{ctx.stem}_probability_density_table_{table_index + 1}.csv")

    nums = numeric_columns(df)
    if len(nums) >= 2:
        x_col = st.selectbox("X axis for PDF chart", nums, index=0, key="pdf_x")
        y_cols = st.multiselect(
            "Y columns for PDF chart",
            [c for c in nums if c != x_col],
            default=[c for c in nums if c != x_col][:2],
            key="pdf_y",
        )
        if y_cols:
            plot_df = df[[x_col] + y_cols].melt(id_vars=[x_col], value_vars=y_cols, var_name="Series", value_name="Value")
            plotly_view(px.line(plot_df, x=x_col, y="Value", color="Series", markers=True))


def _render_manual_table(ctx) -> None:
    st.subheader("Manual Table Extraction")
    st.write("Use this when the auto-parser misses a table or merges sections incorrectly.")

    total_lines = len(ctx.parsed.get("lines", []))
    if total_lines == 0:
        st.info("No raw lines are available.")
        return

    c1, c2, c3 = st.columns(3)
    start_line = c1.number_input("Start line", min_value=1, max_value=max(1, total_lines), value=1, step=1)
    end_line = c2.number_input("End line", min_value=1, max_value=max(1, total_lines), value=min(total_lines, 20), step=1)
    use_header = c3.checkbox("Use a header line", value=True)
    header_line = None
    if use_header:
        header_line = st.number_input(
            "Header line",
            min_value=int(start_line),
            max_value=max(int(start_line), int(end_line)),
            value=int(start_line),
            step=1,
        )

    st.markdown("#### Raw line preview")
    dataframe_view(preview_lines(ctx.parsed.get("lines", []), int(start_line), int(end_line)))

    # Manual tables are keyed by the full uploaded filename (current_name),
    # matching the convention used everywhere else (derived columns, units,
    # notes). v25 used the file *stem* here, which meant a manual table
    # promoted for "run1.out" was stored under a different key than the one
    # the Report Builder's "Manual Tables" section looked up.
    if st.button("Parse selected line range"):
        try:
            manual_df = parse_manual_table(
                ctx.parsed.get("lines", []),
                int(start_line),
                int(end_line),
                header_line=int(header_line) if use_header else None,
            )
            if manual_df.empty:
                st.warning("No table was parsed from that line range.")
            else:
                st.session_state.setdefault("manual_tables", {})
                st.session_state["manual_tables"].setdefault(ctx.current_name, {})
                section_name = f"Manual lines {int(start_line)}-{int(end_line)}"
                st.session_state["manual_tables"][ctx.current_name][section_name] = manual_df
                st.session_state[f"manual_table_active_{ctx.current_name}"] = section_name
                st.success(f"Parsed and promoted manual table: {len(manual_df)} rows × {len(manual_df.columns)} columns")
        except Exception as exc:
            st.error(f"Manual parse failed: {exc}")

    manual_sections = st.session_state.get("manual_tables", {}).get(ctx.current_name, {})
    if manual_sections:
        st.markdown("#### Parsed Manual Tables")
        section_names = list(manual_sections.keys())
        default_section = st.session_state.get(f"manual_table_active_{ctx.current_name}", section_names[-1])
        default_index = section_names.index(default_section) if default_section in section_names else len(section_names) - 1
        chosen = st.selectbox("Manual table", section_names, index=default_index, key="manual_table_view_select")
        manual_df = manual_sections[chosen]
        dataframe_view(manual_df)
        build_download_button("Download manual table as CSV", manual_df, f"{ctx.stem}_manual_table.csv")
