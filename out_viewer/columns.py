from typing import List, Optional, Tuple

import pandas as pd

from .constants import INDEX_NAMES, NON_SERIES_NAMES
from .parser import DetectedTable


def main_tables(tables: List[DetectedTable]) -> List[DetectedTable]:
    return [table for table in tables if table.kind == "main"]


def probability_tables(tables: List[DetectedTable]) -> List[DetectedTable]:
    return [table for table in tables if table.kind == "probability"]


def main_table(tables: List[DetectedTable]):
    candidates = main_tables(tables)
    return max(candidates, key=lambda table: len(table.data)) if candidates else None


def numeric_columns(df: pd.DataFrame):
    return [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]


def preferred_x(df: pd.DataFrame):
    nums = numeric_columns(df)
    for column in df.columns:
        if column.lower() in INDEX_NAMES and column in nums:
            return column
    return nums[0] if nums else None


def default_y_columns(df: pd.DataFrame, x_col):
    nums = [column for column in numeric_columns(df) if column != x_col]
    preferred = [
        column
        for column in nums
        if column.lower() not in NON_SERIES_NAMES
    ]
    return preferred[: min(3, len(preferred))] if preferred else nums[: min(3, len(nums))]


def safe_float_range(series: pd.Series) -> Optional[Tuple[float, float]]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return None

    min_val = float(numeric.min())
    max_val = float(numeric.max())

    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return None

    return min_val, max_val


def table_options(tables: List[DetectedTable], *, require_numeric_cols: int = 0):
    output = []
    for table in tables:
        if require_numeric_cols and len(numeric_columns(table.data)) < require_numeric_cols:
            continue
        output.append(table)
    return output
