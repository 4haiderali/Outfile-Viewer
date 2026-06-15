"""Analysis tab: everything statistical lives here as sub-tabs.

v25 spread this across six top-level tabs (Statistics, Distribution,
Insights, Advanced Insights, Analytics, Charts) with real overlap --
"Risk Ranking" and "Extended Statistics" appeared on both Cockpit and
Insights, and PCA-based multivariate outliers appeared on Findings,
Advanced Insights, *and* as a Charts chart type. Here:

- Statistics: detected metric rows, descriptive stats, and extended
  (unit-aware) statistics for a chosen table.
- Distribution: shape diagnostics + convergence/stabilization.
- Outliers & Ranking: z-score outliers, top/bottom ranking, and the
  deep-dive PCA view (projection figure, loadings, multivariate outlier
  table) for a user-chosen set of columns.
- Charts: the full dynamic chart picker, including a PCA Projection chart
  type for quick visual exploration.

The PCA Projection *chart type* and the Outliers & Ranking PCA *table* both
remain because they serve different purposes (visual exploration vs.
exporting a configurable outlier table + loadings) -- but everything else
that was duplicated across the old tabs now appears exactly once.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..advanced_insights import multivariate_outliers, pca_figure, pca_projection
from ..analytics import describe_table, get_outliers, ranking_table
from ..cockpit import extended_statistics
from ..columns import default_y_columns, numeric_columns, preferred_x, table_options
from ..constants import INDEX_NAMES
from ..diagnostics import convergence_summary, distribution_diagnostics, stabilization_run
from ..session_data import get_session_table
from ..ui_helpers import build_download_button, dataframe_view, plotly_view, styled_dataframe_view
from ..units import stats_with_units


def _table_picker(ctx, tables, *, key: str, label: str = "Table"):
    names = [
        f"{i + 1}. {t.name} [{t.kind}] — "
        f"{len(get_session_table(t, ctx.current_name))} rows × {len(get_session_table(t, ctx.current_name).columns)} columns"
        for i, t in enumerate(tables)
    ]
    selected = st.selectbox(label, names, key=key)
    table = tables[names.index(selected)]
    return table, get_session_table(table, ctx.current_name)


def render(ctx) -> None:
    sub_stats, sub_dist, sub_outliers, sub_charts = st.tabs(
        ["Statistics", "Distribution", "Outliers & Ranking", "Charts"]
    )

    with sub_stats:
        _render_statistics(ctx)

    with sub_dist:
        _render_distribution(ctx)

    with sub_outliers:
        _render_outliers_ranking(ctx)

    with sub_charts:
        _render_charts(ctx)


def _render_statistics(ctx) -> None:
    if not ctx.stats_df.empty:
        st.subheader("Detected Statistics / Metric Rows")
        dataframe_view(ctx.stats_df.copy())
        build_download_button("Download statistics as CSV", ctx.stats_df.copy(), f"{ctx.stem}_statistics.csv")

    stat_tables = table_options(ctx.tables, require_numeric_cols=1)
    if not stat_tables:
        st.info("No numeric tables available for descriptive or extended statistics.")
        return

    table, df = _table_picker(ctx, stat_tables, key="stats_table_select")

    st.markdown("#### Descriptive Statistics")
    desc = describe_table(df)
    if desc.empty:
        st.warning("No numeric columns to describe.")
    else:
        styled_dataframe_view(desc, preset="numeric", hide_index=False)
        build_download_button("Download descriptive statistics as CSV", desc.reset_index(names="Column"), f"{ctx.stem}_describe.csv")

    st.markdown("#### Extended Statistics (with tagged units)")
    ext = extended_statistics(df)
    if ext.empty:
        st.info("No numeric columns available for extended statistics.")
    else:
        ext_with_units = stats_with_units(ext, ctx.unit_map)
        styled_dataframe_view(ext_with_units, preset="numeric")
        build_download_button("Download extended statistics", ext_with_units, f"{ctx.stem}_extended_statistics.csv")
        st.caption("Tag units for these columns on the Derived & Units tab to have them carried through here and into reports.")


def _render_distribution(ctx) -> None:
    diagnostic_tables = table_options(ctx.tables, require_numeric_cols=1)
    if not diagnostic_tables:
        st.info("No numeric tables available for distribution diagnostics.")
        return

    table, df = _table_picker(ctx, diagnostic_tables, key="distribution_table_select")

    st.subheader("Distribution Diagnostics")
    diag = distribution_diagnostics(df)
    if diag.empty:
        st.info("Not enough numeric data for diagnostics.")
    else:
        styled_dataframe_view(diag, preset="numeric")
        build_download_button("Download distribution diagnostics", diag, f"{ctx.stem}_distribution_diagnostics.csv")

    st.markdown("#### Convergence Stabilization Summary")
    tol = st.number_input("Stabilization tolerance %", min_value=0.1, value=1.0, step=0.1, key="dist_conv_tol")
    tail = st.number_input("Tail run requirement", min_value=3, value=10, step=1, key="dist_conv_tail")
    conv_summary = convergence_summary(df, tolerance_pct=float(tol), min_tail=int(tail))
    if conv_summary.empty:
        st.info("No convergence summary available.")
    else:
        dataframe_view(conv_summary)
        build_download_button("Download convergence summary", conv_summary, f"{ctx.stem}_convergence_summary.csv")


def _render_outliers_ranking(ctx) -> None:
    analysis_tables = table_options(ctx.tables, require_numeric_cols=1)
    if not analysis_tables:
        st.info("No numeric tables available for outliers or ranking.")
        return

    table, df = _table_picker(ctx, analysis_tables, key="outliers_ranking_table_select")
    nums = numeric_columns(df)

    sub_z, sub_rank, sub_pca = st.tabs(["Z-Score Outliers", "Ranking", "Multivariate (PCA)"])

    with sub_z:
        selected_cols = st.multiselect("Columns", nums, default=default_y_columns(df, preferred_x(df)), key="outlier_cols")
        sigma = st.selectbox("Sigma threshold", [1.5, 2.0, 2.5, 3.0], index=1, key="outlier_sigma")
        if selected_cols:
            outliers = get_outliers(df, selected_cols, sigma)
            st.metric("Outlier rows", len(outliers))
            if outliers.empty:
                st.success("No outliers found for the selected threshold.")
            else:
                dataframe_view(outliers)
                build_download_button("Download outliers as CSV", outliers, f"{ctx.stem}_outliers.csv")

    with sub_rank:
        rank_col = st.selectbox("Rank by column", nums, key="rank_col")
        n = st.number_input("Rows to show", min_value=1, max_value=max(1, len(df)), value=min(10, len(df)), step=1, key="rank_n")
        direction = st.radio("Direction", ["Highest", "Lowest"], horizontal=True, key="rank_direction")
        ranked = ranking_table(df, rank_col, int(n), direction)
        dataframe_view(ranked)
        build_download_button("Download ranking as CSV", ranked, f"{ctx.stem}_ranking_{rank_col}.csv")

    with sub_pca:
        pca_candidates = [c for c in nums if str(c).lower() not in INDEX_NAMES]
        selected_cols = st.multiselect(
            "Analysis columns",
            pca_candidates,
            default=pca_candidates[: min(8, len(pca_candidates))],
            key="pca_columns",
        )
        if len(selected_cols) < 2:
            st.info("Select at least two analysis columns.")
        else:
            projection, loadings = pca_projection(df, selected_cols)
            if projection.empty:
                st.info("Not enough complete rows for a PCA-style projection.")
            else:
                fig = pca_figure(projection)
                if fig is not None:
                    plotly_view(fig)

                st.markdown("#### Top Multivariate Outlier Rows")
                outliers = multivariate_outliers(df, selected_cols)
                styled_dataframe_view(outliers, preset="numeric")
                build_download_button("Download PCA outlier rows", outliers, f"{ctx.stem}_pca_outliers.csv")

                st.markdown("#### Principal Component Loadings")
                styled_dataframe_view(loadings, preset="numeric")
                build_download_button("Download PCA loadings", loadings, f"{ctx.stem}_pca_loadings.csv")


def _render_charts(ctx) -> None:
    chart_tables = table_options(ctx.tables, require_numeric_cols=2)
    if not chart_tables:
        st.info("Need a table with at least two numeric columns to build charts.")
        return

    table, df = _table_picker(ctx, chart_tables, key="chart_table_select")
    nums = numeric_columns(df)

    chart_type = st.selectbox(
        "Chart type",
        [
            "Line", "Scatter", "Bar", "Histogram", "CDF", "Box Plot", "Percentile Band",
            "Run Profile", "PCA Projection", "Correlation Heatmap", "Run × Column Heatmap",
            "Convergence Tracker",
        ],
        key="chart_type",
    )

    if chart_type in {"Line", "Scatter", "Bar"}:
        c1, c2 = st.columns([1, 2])
        default_x = preferred_x(df)
        x_col = c1.selectbox("X axis", nums, index=nums.index(default_x) if default_x in nums else 0, key="chart_x")
        y_candidates = [c for c in nums if c != x_col]
        y_cols = c2.multiselect("Y columns", y_candidates, default=default_y_columns(df, x_col), key="chart_y")
        if y_cols:
            plot_df = df[[x_col] + y_cols].melt(id_vars=[x_col], value_vars=y_cols, var_name="Series", value_name="Value")
            if chart_type == "Line":
                fig = px.line(plot_df, x=x_col, y="Value", color="Series", markers=True)
            elif chart_type == "Scatter":
                fig = px.scatter(plot_df, x=x_col, y="Value", color="Series")
            else:
                fig = px.bar(plot_df, x=x_col, y="Value", color="Series", barmode="group")
            plotly_view(fig)

    elif chart_type == "Histogram":
        col = st.selectbox("Column", nums, key="hist_col")
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if values.empty:
            st.warning("Selected column has no numeric values.")
        else:
            fig = px.histogram(values, x=col, nbins=min(40, max(5, len(values) // 5)), marginal="box")
            for pct in [5, 50, 95]:
                xv = float(np.percentile(values, pct))
                fig.add_vline(x=xv, line_dash="dash", annotation_text=f"P{pct}={xv:.4g}")
            plotly_view(fig)

    elif chart_type == "CDF":
        col = st.selectbox("Column", nums, key="cdf_col")
        values = pd.to_numeric(df[col], errors="coerce").dropna().sort_values().values
        if len(values) == 0:
            st.warning("Selected column has no numeric values.")
        else:
            cdf = np.arange(1, len(values) + 1) / len(values) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=values, y=cdf, mode="lines", name="CDF"))
            for pct in [5, 50, 95]:
                xv = float(np.percentile(values, pct))
                fig.add_vline(x=xv, line_dash="dot", annotation_text=f"P{pct}={xv:.4g}")
            fig.add_hline(y=95, line_dash="dot", annotation_text="95%")
            fig.update_layout(title=f"CDF: {col}", xaxis_title=col, yaxis_title="Cumulative %")
            plotly_view(fig)

    elif chart_type == "Box Plot":
        selected_cols = st.multiselect("Columns", nums, default=default_y_columns(df, preferred_x(df)), key="box_cols")
        if selected_cols:
            plotly_view(
                px.box(
                    df[selected_cols].melt(var_name="Column", value_name="Value"),
                    x="Column", y="Value", points="outliers", title="Box Plot",
                )
            )

    elif chart_type == "Percentile Band":
        selected_cols = st.multiselect("Columns", nums, default=default_y_columns(df, preferred_x(df)), key="pctband_cols")
        if selected_cols:
            rows = []
            for col in selected_cols:
                values = pd.to_numeric(df[col], errors="coerce").dropna()
                if values.empty:
                    continue
                for pct in [0, 5, 50, 95, 100]:
                    label = "Min" if pct == 0 else "Max" if pct == 100 else f"P{pct}"
                    rows.append({"Column": col, "Percentile": label, "Value": float(np.percentile(values, pct))})
            pct_df = pd.DataFrame(rows)
            if not pct_df.empty:
                fig = px.line(pct_df, x="Percentile", y="Value", color="Column", markers=True, title="Percentile Band")
                plotly_view(fig)

    elif chart_type == "Run Profile":
        x_default = preferred_x(df)
        if x_default is None:
            st.info("No run/index column available.")
        else:
            run_values = list(pd.to_numeric(df[x_default], errors="coerce").dropna().unique())
            if not run_values:
                st.info("No run values available.")
            else:
                selected_run = st.selectbox("Run / index value", run_values, key="run_profile_run")
                selected_cols = st.multiselect(
                    "Profile columns", [c for c in nums if c != x_default],
                    default=default_y_columns(df, x_default), key="run_profile_cols",
                )
                row = df[pd.to_numeric(df[x_default], errors="coerce") == selected_run]
                if selected_cols and not row.empty:
                    profile = pd.DataFrame({
                        "Column": selected_cols,
                        "Value": [float(pd.to_numeric(row[c], errors="coerce").iloc[0]) for c in selected_cols],
                    })
                    fig = px.bar(profile, x="Column", y="Value", title=f"Run Profile: {x_default}={selected_run}")
                    plotly_view(fig)

    elif chart_type == "PCA Projection":
        candidates = [c for c in nums if str(c).lower() not in INDEX_NAMES]
        selected_cols = st.multiselect(
            "Columns", candidates,
            default=candidates[: min(8, len(candidates))],
            key="chart_pca_cols",
        )
        if len(selected_cols) < 2:
            st.info("Select at least two columns.")
        else:
            projection, loadings = pca_projection(df, selected_cols)
            fig = pca_figure(projection)
            if fig is None:
                st.info("Not enough complete rows for PCA projection.")
            else:
                plotly_view(fig)
                with st.expander("PCA loadings"):
                    styled_dataframe_view(loadings, preset="numeric")

    elif chart_type == "Correlation Heatmap":
        selected_cols = st.multiselect("Columns", nums, default=nums[: min(8, len(nums))], key="corr_cols")
        if len(selected_cols) >= 2:
            corr = df[selected_cols].apply(pd.to_numeric, errors="coerce").corr().round(3)
            plotly_view(px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="Correlation Matrix"))
        else:
            st.info("Select at least two columns.")

    elif chart_type == "Run × Column Heatmap":
        selected_cols = st.multiselect("Columns", nums, default=default_y_columns(df, preferred_x(df)), key="heat_cols")
        if selected_cols:
            matrix = df[selected_cols].apply(pd.to_numeric, errors="coerce")
            normalized = (matrix - matrix.mean()) / matrix.std().replace(0, np.nan)
            plotly_view(px.imshow(normalized.fillna(0), aspect="auto", color_continuous_scale="RdBu_r", title="Run × Column Heatmap (z-score normalized)"))

    elif chart_type == "Convergence Tracker":
        col = st.selectbox("Column", nums, key="conv_col")
        window = st.number_input("Rolling window", min_value=2, max_value=max(2, len(df)), value=min(50, max(2, len(df))), step=1, key="conv_window")
        values = pd.to_numeric(df[col], errors="coerce")
        conv = pd.DataFrame({"Run": range(1, len(values) + 1), col: values})
        conv["Rolling Mean"] = values.rolling(int(window), min_periods=1).mean()
        conv["Rolling Std"] = values.rolling(int(window), min_periods=1).std()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=conv["Run"], y=conv[col], mode="markers", name="Raw", opacity=0.45))
        fig.add_trace(go.Scatter(x=conv["Run"], y=conv["Rolling Mean"], mode="lines", name="Rolling Mean"))
        fig.add_trace(go.Scatter(x=conv["Run"], y=conv["Rolling Mean"] + conv["Rolling Std"], mode="lines", name="+1σ", line=dict(dash="dot")))
        fig.add_trace(go.Scatter(x=conv["Run"], y=conv["Rolling Mean"] - conv["Rolling Std"], mode="lines", name="-1σ", line=dict(dash="dot")))
        stable_at = stabilization_run(values, tolerance_pct=1.0, min_tail=max(3, int(window)))
        if stable_at is not None:
            fig.add_vline(x=stable_at, line_dash="dash", annotation_text=f"Stable ~ run {stable_at}", annotation_position="top")
            st.success(f"Stabilization marker: approximately run {stable_at} using 1% tolerance.")
        else:
            st.info("No stabilization point detected with the default 1% tolerance.")
        fig.update_layout(title=f"Convergence Tracker: {col}", xaxis_title="Run", yaxis_title=col)
        plotly_view(fig)
