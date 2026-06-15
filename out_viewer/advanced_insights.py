"""Advanced analysis helpers: narratives, PCA-style projection, multivariate outliers."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px

from .constants import INDEX_NAMES


def analysis_columns(df: pd.DataFrame, max_columns: int = 12) -> list[str]:
    cols = [
        str(c)
        for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and str(c).lower() not in INDEX_NAMES
    ]
    return cols[:max_columns]


def narrative_findings(df: pd.DataFrame, risk_df: pd.DataFrame, file_name: str) -> list[str]:
    findings = []
    cols = analysis_columns(df)

    findings.append(f"Loaded **{file_name}** with **{len(df):,} rows** and **{len(cols):,} numeric analysis variable(s)**.")

    if not risk_df.empty:
        top = risk_df.iloc[0]
        findings.append(
            f"Highest unitless risk variable: **{top['Column']}** "
            f"(score **{float(top['Risk Score']):.1f}**, relative range **{float(top.get('Relative Range %', 0)):.2f}%**)."
        )

    if cols:
        numeric = df[cols].apply(pd.to_numeric, errors="coerce")
        missing = numeric.isna().sum().sum()
        if missing:
            findings.append(f"Detected **{int(missing):,} missing numeric value(s)** in the selected analysis columns.")
        else:
            findings.append("No missing numeric values were detected in the selected analysis columns.")

        corr = numeric.corr().abs()
        pairs = []
        for i, a in enumerate(corr.columns):
            for b in corr.columns[i + 1:]:
                val = corr.loc[a, b]
                if pd.notna(val):
                    pairs.append((float(val), a, b))
        if pairs:
            val, a, b = sorted(pairs, reverse=True)[0]
            findings.append(f"Strongest absolute correlation: **{a}** vs **{b}** with |r| = **{val:.3f}**.")

    return findings


def pca_projection(df: pd.DataFrame, columns: Iterable[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = list(columns) if columns else analysis_columns(df)
    if len(cols) < 2:
        return pd.DataFrame(), pd.DataFrame()

    x = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 3:
        return pd.DataFrame(), pd.DataFrame()

    z = (x - x.mean()) / x.std().replace(0, np.nan)
    z = z.fillna(0)

    # SVD PCA without external dependencies.
    u, s, vt = np.linalg.svd(z.values, full_matrices=False)
    scores = u[:, :2] * s[:2]
    explained = (s ** 2) / max(1, (len(z) - 1))
    explained_ratio = explained / explained.sum() if explained.sum() else explained

    projection = pd.DataFrame(
        {
            "Row": z.index,
            "PC1": scores[:, 0],
            "PC2": scores[:, 1] if scores.shape[1] > 1 else 0.0,
        }
    )
    projection["Distance"] = np.sqrt(projection["PC1"] ** 2 + projection["PC2"] ** 2)
    projection["Outlier Rank"] = projection["Distance"].rank(ascending=False, method="dense").astype(int)

    loadings = pd.DataFrame(
        {
            "Column": cols,
            "PC1 Loading": vt[0, :],
            "PC2 Loading": vt[1, :] if len(vt) > 1 else np.zeros(len(cols)),
        }
    )
    loadings["Abs PC1"] = loadings["PC1 Loading"].abs()
    loadings["Abs PC2"] = loadings["PC2 Loading"].abs()
    loadings.attrs["explained_ratio"] = explained_ratio[:2].tolist()

    return projection.sort_values("Outlier Rank"), loadings.sort_values("Abs PC1", ascending=False)


def pca_figure(projection: pd.DataFrame):
    if projection.empty:
        return None
    return px.scatter(
        projection,
        x="PC1",
        y="PC2",
        color="Distance",
        hover_data=["Row", "Outlier Rank"],
        title="PCA / Multivariate Outlier Projection",
    )


def multivariate_outliers(df: pd.DataFrame, columns: Iterable[str] | None = None, top_n: int = 20) -> pd.DataFrame:
    projection, _ = pca_projection(df, columns)
    if projection.empty:
        return projection
    return projection.sort_values("Distance", ascending=False).head(top_n).reset_index(drop=True)
