import numpy as np
import pandas as pd

from .columns import numeric_columns


def describe_table(df: pd.DataFrame) -> pd.DataFrame:
    nums = numeric_columns(df)
    if not nums:
        return pd.DataFrame()

    numeric_df = df[nums].apply(pd.to_numeric, errors="coerce")
    desc = numeric_df.describe(percentiles=[0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]).T
    desc["range"] = desc["max"] - desc["min"]
    desc["cv_pct"] = (desc["std"] / desc["mean"].abs() * 100).replace([np.inf, -np.inf], np.nan)
    return desc.round(6)


def get_outliers(df: pd.DataFrame, cols, sigma: float) -> pd.DataFrame:
    numeric_df = df[cols].apply(pd.to_numeric, errors="coerce")
    std = numeric_df.std().replace(0, np.nan)
    z = (numeric_df - numeric_df.mean()) / std

    mask = (z.abs() > sigma).any(axis=1)
    if not mask.any():
        return pd.DataFrame()

    out = df.loc[mask].copy()
    out["worst_col"] = z.loc[mask].abs().idxmax(axis=1)
    out["worst_zscore"] = z.loc[mask].abs().max(axis=1).round(3)
    return out.sort_values("worst_zscore", ascending=False)


def ranking_table(df: pd.DataFrame, col: str, n: int, direction: str) -> pd.DataFrame:
    numeric = pd.to_numeric(df[col], errors="coerce")
    temp = df.copy()
    temp["_rank_value"] = numeric
    ascending = direction == "Lowest"
    ranked = temp.sort_values("_rank_value", ascending=ascending).head(n).copy()
    ranked.insert(0, "Rank", range(1, len(ranked) + 1))
    return ranked.drop(columns=["_rank_value"])


def apply_numeric_filters(df: pd.DataFrame, ranges: dict) -> pd.DataFrame:
    if not ranges:
        return df

    mask = pd.Series(True, index=df.index)
    for column, selected_range in ranges.items():
        numeric = pd.to_numeric(df[column], errors="coerce")
        mask &= numeric.between(selected_range[0], selected_range[1], inclusive="both")

    return df[mask]
