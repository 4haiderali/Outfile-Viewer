"""Reports tab: the quick enhanced report, a custom section-picker report
builder, and the multi-file batch report -- all three now share one
stylesheet/table-renderer via :mod:`out_viewer.html_report` (see that
module's docstring for why there used to be three separate inline
stylesheets here).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..advanced_insights import narrative_findings
from ..batch import build_batch_html_report, build_batch_risk_table, build_batch_summary
from ..cockpit import build_enhanced_html_report, extended_statistics, variable_risk_ranking
from ..diagnostics import distribution_diagnostics
from ..notes import notes_key, notes_to_dataframe
from ..report_builder import build_sectioned_report, df_section
from ..session_data import get_session_table
from ..ui_helpers import build_download_button, styled_dataframe_view
from ..units import stats_with_units, unit_table
from ..visuals import data_fingerprint_figure, risk_bar_figure


def render(ctx) -> None:
    sub_quick, sub_builder, sub_batch = st.tabs(["Quick Report", "Report Builder", "Batch Report"])

    with sub_quick:
        _render_quick_report(ctx)

    with sub_builder:
        _render_report_builder(ctx)

    with sub_batch:
        _render_batch(ctx)


def _render_quick_report(ctx) -> None:
    st.subheader("Enhanced Engineering Report")
    st.write("Generate a polished HTML report with snapshot, explanation, risk ranking, statistics, metadata, and table preview.")

    primary_df = get_session_table(ctx.primary_table, ctx.current_name) if ctx.primary_table is not None else None
    findings = narrative_findings(primary_df, variable_risk_ranking(primary_df), ctx.current_name) if primary_df is not None else []

    report_bytes = build_enhanced_html_report(
        ctx.current_name,
        ctx.parsed,
        ctx.tables,
        unit_map=ctx.unit_map,
        file_count=ctx.file_count,
        findings=findings,
    )
    st.download_button("Download HTML report", data=report_bytes, file_name=f"{ctx.stem}_summary_report.html", mime="text/html")
    st.caption("HTML preview is disabled here to keep the console clean; use the download button to open the report in your browser.")


def _render_report_builder(ctx) -> None:
    st.subheader("Report Builder")
    st.write("Select sections and embed key Plotly charts into a shareable HTML report.")

    selected_sections = st.multiselect(
        "Report sections",
        ["Narrative Findings", "Risk Ranking", "Extended Statistics", "Distribution Diagnostics", "Unit Tags", "Notes", "Manual Tables"],
        default=["Narrative Findings", "Risk Ranking", "Extended Statistics", "Distribution Diagnostics", "Unit Tags", "Notes"],
    )
    include_figures = st.checkbox("Embed cockpit charts", value=True)

    if ctx.primary_table is None:
        st.info("No primary numeric table was detected.")
        return

    primary_df = get_session_table(ctx.primary_table, ctx.current_name)
    sections: dict[str, str] = {}
    report_notes = notes_to_dataframe(st.session_state.get(notes_key(ctx.current_name), []))
    risk_df = variable_risk_ranking(primary_df)

    if "Narrative Findings" in selected_sections:
        findings = narrative_findings(primary_df, risk_df, ctx.current_name)
        sections["Narrative Findings"] = "<ul>" + "".join(f"<li>{item}</li>" for item in findings) + "</ul>"
    if "Risk Ranking" in selected_sections:
        sections["Risk Ranking"] = df_section(risk_df)
    if "Extended Statistics" in selected_sections:
        ext_stats = stats_with_units(extended_statistics(primary_df), ctx.unit_map)
        sections["Extended Statistics"] = df_section(ext_stats)
    if "Distribution Diagnostics" in selected_sections:
        sections["Distribution Diagnostics"] = df_section(distribution_diagnostics(primary_df))
    if "Unit Tags" in selected_sections:
        sections["Unit Tags"] = df_section(unit_table(ctx.unit_map.keys(), ctx.unit_map))
    if "Manual Tables" in selected_sections:
        manual_sections = st.session_state.get("manual_tables", {}).get(ctx.current_name, {})
        if manual_sections:
            sections["Manual Tables"] = "".join(
                f"<h3>{name}</h3>{df_section(df)}" for name, df in manual_sections.items()
            )
        else:
            sections["Manual Tables"] = "<p>No manual tables promoted for this file.</p>"

    embedded = []
    if include_figures:
        risk_fig = risk_bar_figure(risk_df)
        fp_fig = data_fingerprint_figure(primary_df)
        for fig in [risk_fig, fp_fig]:
            if fig is not None:
                embedded.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    report_bytes = build_sectioned_report(
        title=f"{ctx.current_name} Engineering Report",
        sections=sections,
        notes=report_notes if "Notes" in selected_sections else pd.DataFrame(),
        embedded_figures=embedded,
    )
    st.download_button(
        "Download custom HTML report",
        data=report_bytes,
        file_name=f"{ctx.stem}_custom_engineering_report.html",
        mime="text/html",
    )


def _render_batch(ctx) -> None:
    st.subheader("Batch Summary / Report")
    history = st.session_state.get("file_history", {})
    if not history:
        st.info("No files loaded.")
        return

    summary = build_batch_summary(history)
    risk = build_batch_risk_table(history)

    st.markdown("#### File-Level Batch Summary")
    styled_dataframe_view(summary, preset="numeric")
    build_download_button("Download batch summary", summary, "out_viewer_batch_summary.csv")

    st.markdown("#### Top Risk Variables by File")
    if risk.empty:
        st.info("No risk tables available.")
    else:
        styled_dataframe_view(risk, preset="risk")
        build_download_button("Download batch risk table", risk, "out_viewer_batch_risk.csv")

    report_bytes = build_batch_html_report(summary, risk)
    st.download_button(
        "Download batch HTML report",
        data=report_bytes,
        file_name="out_viewer_batch_report.html",
        mime="text/html",
    )
