from typing import Any, Dict, List

import pandas as pd


TEXT_OPERATORS = ["contains", "not contains", "equals", "not equals"]
NUMERIC_OPERATORS = [">", ">=", "<", "<=", "=", "!="]


def apply_condition(df: pd.DataFrame, column: str, operator: str, value: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)

    series = df[column]

    if operator in TEXT_OPERATORS:
        text_series = series.astype(str)
        value_text = str(value)

        if operator == "contains":
            return text_series.str.contains(value_text, case=False, na=False, regex=False)
        if operator == "not contains":
            return ~text_series.str.contains(value_text, case=False, na=False, regex=False)
        if operator == "equals":
            return text_series.str.lower() == value_text.lower()
        if operator == "not equals":
            return text_series.str.lower() != value_text.lower()

    numeric_series = pd.to_numeric(series, errors="coerce")
    try:
        numeric_value = float(value)
    except Exception:
        return pd.Series(False, index=df.index)

    if operator == ">":
        return numeric_series > numeric_value
    if operator == ">=":
        return numeric_series >= numeric_value
    if operator == "<":
        return numeric_series < numeric_value
    if operator == "<=":
        return numeric_series <= numeric_value
    if operator == "=":
        return numeric_series == numeric_value
    if operator == "!=":
        return numeric_series != numeric_value

    return pd.Series(False, index=df.index)


def apply_conditions(df: pd.DataFrame, conditions: List[Dict[str, Any]], joiner: str = "AND") -> pd.DataFrame:
    valid_conditions = [
        condition
        for condition in conditions
        if condition.get("column") and condition.get("operator") and str(condition.get("value", "")).strip() != ""
    ]

    if not valid_conditions:
        return df.copy()

    masks = [
        apply_condition(df, condition["column"], condition["operator"], condition["value"])
        for condition in valid_conditions
    ]

    if joiner == "OR":
        combined = pd.Series(False, index=df.index)
        for mask in masks:
            combined |= mask
    else:
        combined = pd.Series(True, index=df.index)
        for mask in masks:
            combined &= mask

    return df.loc[combined].copy()


def condition_summary(conditions: List[Dict[str, Any]], joiner: str = "AND") -> str:
    pieces = []
    for condition in conditions:
        column = condition.get("column")
        operator = condition.get("operator")
        value = condition.get("value")
        if column and operator and str(value).strip() != "":
            pieces.append(f"{column} {operator} {value}")

    if not pieces:
        return "No active advanced filter conditions."

    return f" {joiner} ".join(pieces)
