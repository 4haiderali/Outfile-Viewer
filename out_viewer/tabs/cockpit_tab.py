"""Cockpit tab: study snapshot, plain-English summary, narrative findings,
variable risk ranking, data fingerprint, multivariate outlier snapshot, and
quick actions.

This merges what were two separate v25 tabs ("Cockpit" and "Findings") --
both were "first thing an engineer reads about this dataset" content, so
splitting them into different tabs just meant clicking back and forth.
"""

from __future__ import annotations

import streamlit as st

from ..advanced_insights import multivariate_outliers, narrative_findings
from ..cockpit import explain_dataset, recommended_next_steps, study_snapshot, variable_risk_ranking
from ..ui_helpers import build_download_button, plotly_view, styled_dataframe_view
from ..visuals import data_fingerprint_figure, risk_bar_figure
from ..session_data import get_session_table


def render(ctx) -> None:
    st.subheader("Engineering Cockpit")

    snap = study_snapshot(ctx.parsed, ctx.tables, ctx.current_name)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Parse Status", str(snap.get("Status", "Unknown")))
    c2.metric("Primary Rows", f"{int(snap.get('Primary Rows', 0)):,}")
    c3.metric("Primary Columns", f"{int(snap.get('Primary Columns', 0)):,}")
    c4.metric("Highest Risk Variable", str(snap.get("Highest Risk Variable", "N/A")))

    st.markdown("#### Plain-English Summary")
    st.info(explain_dataset(ctx.parsed, ctx.tables, ctx.current_name, ctx.file_count))

    primary_df = get_session_table(ctx.primary_table, ctx.current_name) if ctx.primary_table is not None else None
    risk_df = variable_risk_ranking(primary_df) if primary_df is not None else None

    st.markdown("#### Narrative Findings")
    if primary_df is None:
        st.info("No primary numeric table was detected, so there are no narrative findings yet.")
    else:
        findings = narrative_findings(primary_df, risk_df, ctx.current_name)
        for item in findings:
            st.markdown(f"- {item}")

    st.markdown("#### Recommended Next Steps")
    for step in recommended_next_steps(ctx.parsed, ctx.tables, ctx.file_count):
        st.write(f"✅ {step}")

    if primary_df is not None and risk_df is not None:
        st.markdown("#### Variable Risk Ranking")
        if risk_df.empty:
            st.info("No numeric variables available for risk ranking.")
        else:
            styled_dataframe_view(risk_df.head(12), preset="risk")
            risk_fig = risk_bar_figure(risk_df)
            if risk_fig is not None:
                plotly_view(risk_fig)
            build_download_button("Download variable risk ranking", risk_df, f"{ctx.stem}_variable_risk_ranking.csv")

        st.markdown("#### Data Fingerprint")
        fp_fig = data_fingerprint_figure(primary_df)
        if fp_fig is None:
            st.info("No numeric variables available for a visual fingerprint.")
        else:
            plotly_view(fp_fig)

        st.markdown("#### Multivariate Outlier Snapshot")
        st.caption("A quick top-12 view based on every numeric analysis column. For a configurable, deeper "
                   "dive (choose columns, see PCA loadings and the projection plot), use Analysis → Outliers & Ranking.")
        outliers = multivariate_outliers(primary_df)
        if outliers.empty:
            st.info("Need at least two numeric analysis columns and three complete rows for multivariate outliers.")
        else:
            styled_dataframe_view(outliers.head(12), preset="numeric")
            build_download_button("Download multivariate outliers", outliers, f"{ctx.stem}_multivariate_outliers.csv")

    st.markdown("#### Quick Actions")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.caption("Data")
        st.write("Browse detected tables, PDF tables, and the summary in the Data tab.")
    with q2:
        st.caption("Analysis")
        st.write("Switch to Analysis for percentiles, distribution checks, risk, charts, and outliers.")
    with q3:
        st.caption("Compliance")
        st.write("Define threshold or custom-expression rules in Compliance.")
    with q4:
        st.caption("Reports")
        st.write("Switch to Reports for an enhanced HTML report or a custom report builder.")
