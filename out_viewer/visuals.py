"""Reusable visual helpers for Cockpit and Analysis."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
import plotly.express as px

from .constants import INDEX_NAMES


def non_index_numeric_columns(df: pd.DataFrame) -> list[str]:
    return [
        str(col)
        for col in df.columns
        if pd.api.types.is_numeric_dtype(df[col]) and str(col).lower() not in INDEX_NAMES
    ]


def data_fingerprint_figure(df: pd.DataFrame, max_columns: int = 12, max_rows: int = 1000):
    cols = non_index_numeric_columns(df)[:max_columns]
    if not cols:
        return None

    matrix = df[cols].apply(pd.to_numeric, errors="coerce").head(max_rows)
    std = matrix.std().replace(0, np.nan)
    normalized = (matrix - matrix.mean()) / std
    normalized = normalized.fillna(0).reset_index(names="Row")
    long = normalized.melt(id_vars=["Row"], var_name="Column", value_name="Normalized Value")

    fig = px.line(
        long,
        x="Row",
        y="Normalized Value",
        facet_col="Column",
        facet_col_wrap=4,
        title="Data Fingerprint — normalized trends by variable",
    )
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_layout(height=max(320, 180 * int(np.ceil(len(cols) / 4))))
    return fig


def risk_bar_figure(risk_df: pd.DataFrame):
    if risk_df.empty or "Risk Score" not in risk_df.columns or "Column" not in risk_df.columns:
        return None

    plot_df = risk_df.head(12).sort_values("Risk Score", ascending=True)
    return px.bar(
        plot_df,
        x="Risk Score",
        y="Column",
        orientation="h",
        title="Top Risk Variables — unitless score",
        hover_data=[c for c in ["Relative Range %", "CV %", "Robust Max Z", "Robust Outlier Count"] if c in plot_df.columns],
    )


def memory_summary_table(file_history: Dict[str, dict]) -> pd.DataFrame:
    rows = []
    for name, record in file_history.items():
        parsed = record.get("parsed", {})
        tables = parsed.get("tables", [])
        rows.append(
            {
                "File": name,
                "Size MB": round(record.get("size", 0) / (1024 * 1024), 3),
                "Lines": len(parsed.get("lines", [])),
                "Tables": len(tables),
            }
        )
    return pd.DataFrame(rows)
