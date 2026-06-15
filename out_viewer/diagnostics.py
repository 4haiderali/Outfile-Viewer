"""Distribution diagnostics and convergence markers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import INDEX_NAMES


def distribution_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    numeric_cols = [
        c for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and str(c).lower() not in INDEX_NAMES
    ]

    for col in numeric_cols:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) < 3:
            continue

        mean = float(s.mean())
        std = float(s.std())
        median = float(s.median())
        skew = float(s.skew()) if len(s) >= 3 else np.nan
        kurtosis = float(s.kurtosis()) if len(s) >= 4 else np.nan

        q1, q3 = np.percentile(s, [25, 75])
        iqr = float(q3 - q1)
        iqr_outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()) if iqr > 0 else 0

        shape_flags = []
        if pd.notna(skew) and abs(skew) > 1:
            shape_flags.append("high skew")
        elif pd.notna(skew) and abs(skew) > 0.5:
            shape_flags.append("moderate skew")

        if pd.notna(kurtosis) and kurtosis > 3:
            shape_flags.append("heavy tails")
        if pd.notna(kurtosis) and kurtosis < -1:
            shape_flags.append("flat/bounded")

        if std == 0:
            shape_flags.append("constant")

        rows.append(
            {
                "Column": col,
                "Count": int(len(s)),
                "Mean": mean,
                "Median": median,
                "Std Dev": std,
                "Skewness": skew,
                "Kurtosis": kurtosis,
                "IQR": iqr,
                "IQR Outliers": iqr_outliers,
                "Shape Flags": ", ".join(shape_flags) if shape_flags else "OK",
            }
        )

    return pd.DataFrame(rows).round(6)


def stabilization_run(values: pd.Series, *, tolerance_pct: float = 1.0, min_tail: int = 10) -> int | None:
    s = pd.to_numeric(values, errors="coerce").dropna().reset_index(drop=True)
    if len(s) < max(5, min_tail + 2):
        return None

    final_mean = float(s.mean())
    if abs(final_mean) < 1e-12:
        scale = max(float(s.abs().max()), 1.0)
    else:
        scale = abs(final_mean)

    cumulative_mean = s.expanding().mean()
    tolerance = scale * tolerance_pct / 100.0

    for idx in range(len(s) - min_tail):
        tail = cumulative_mean.iloc[idx:]
        if ((tail - final_mean).abs() <= tolerance).all():
            return int(idx + 1)

    return None


def convergence_summary(df: pd.DataFrame, tolerance_pct: float = 1.0, min_tail: int = 10) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]) or str(col).lower() in INDEX_NAMES:
            continue
        run = stabilization_run(df[col], tolerance_pct=tolerance_pct, min_tail=min_tail)
        rows.append(
            {
                "Column": col,
                "Stabilization Run": run if run is not None else "Not stable",
                "Tolerance %": tolerance_pct,
                "Tail Requirement": min_tail,
            }
        )
    return pd.DataFrame(rows)
