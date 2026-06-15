"""Baseline/golden-file comparison helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import INDEX_NAMES


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def likely_index_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.columns if str(c).lower() in INDEX_NAMES and pd.api.types.is_numeric_dtype(df[c])]


def shared_numeric_columns(base_df: pd.DataFrame, candidate_df: pd.DataFrame) -> list[str]:
    base = set(numeric_columns(base_df))
    candidate = set(numeric_columns(candidate_df))
    return sorted([c for c in base & candidate if c.lower() not in INDEX_NAMES])


def compare_to_baseline(
    base_name: str,
    candidate_name: str,
    base_df: pd.DataFrame,
    candidate_df: pd.DataFrame,
    *,
    index_col: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    shared = shared_numeric_columns(base_df, candidate_df)
    if not shared:
        return pd.DataFrame(), pd.DataFrame()

    if index_col and index_col in base_df.columns and index_col in candidate_df.columns:
        left = base_df[[index_col] + shared].copy()
        right = candidate_df[[index_col] + shared].copy()
        merged = left.merge(right, on=index_col, suffixes=(f"__{base_name}", f"__{candidate_name}"))
        row_id = index_col
    else:
        n = min(len(base_df), len(candidate_df))
        left = base_df[shared].head(n).reset_index(drop=True).copy()
        right = candidate_df[shared].head(n).reset_index(drop=True).copy()
        merged = left.join(right, lsuffix=f"__{base_name}", rsuffix=f"__{candidate_name}")
        merged.insert(0, "Row", range(n))
        row_id = "Row"

    rows = []
    delta_cols = [row_id]
    for col in shared:
        a = pd.to_numeric(merged[f"{col}__{base_name}"], errors="coerce")
        b = pd.to_numeric(merged[f"{col}__{candidate_name}"], errors="coerce")
        delta = b - a
        delta_pct = np.where(a.abs() > 1e-12, delta / a.abs() * 100, np.nan)

        merged[f"{col} Δ"] = delta
        merged[f"{col} Δ%"] = delta_pct
        delta_cols.extend([f"{col}__{base_name}", f"{col}__{candidate_name}", f"{col} Δ", f"{col} Δ%"])

        delta_pct_series = pd.Series(delta_pct)
        rows.append(
            {
                "Column": col,
                "Rows Compared": int(delta.notna().sum()),
                "Mean Δ": float(delta.mean()) if delta.notna().any() else np.nan,
                "Max |Δ|": float(delta.abs().max()) if delta.notna().any() else np.nan,
                "Mean |Δ%|": float(delta_pct_series.abs().mean()) if delta_pct_series.notna().any() else np.nan,
                "Max |Δ%|": float(delta_pct_series.abs().max()) if delta_pct_series.notna().any() else np.nan,
            }
        )

    summary = pd.DataFrame(rows).sort_values("Max |Δ|", ascending=False).reset_index(drop=True)
    return summary.round(6), merged[delta_cols].round(6)


def baseline_verdict(summary: pd.DataFrame, abs_threshold: float | None = None, pct_threshold: float | None = None) -> pd.DataFrame:
    if summary.empty:
        return summary

    out = summary.copy()
    reasons = []
    statuses = []

    for _, row in out.iterrows():
        row_reasons = []
        if abs_threshold is not None and pd.notna(row.get("Max |Δ|")) and float(row["Max |Δ|"]) > abs_threshold:
            row_reasons.append(f"Max |Δ| > {abs_threshold}")
        if pct_threshold is not None and pd.notna(row.get("Max |Δ%|")) and float(row["Max |Δ%|"]) > pct_threshold:
            row_reasons.append(f"Max |Δ%| > {pct_threshold}")

        reasons.append("; ".join(row_reasons) if row_reasons else "OK")
        statuses.append("FAIL" if row_reasons else "OK")

    out.insert(1, "Verdict", statuses)
    out.insert(2, "Reason", reasons)
    return out
