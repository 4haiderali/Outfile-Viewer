import ast
import re
from typing import Tuple

import numpy as np
import pandas as pd


ALLOWED_FUNCS = {
    "abs": np.abs,
    "sqrt": np.sqrt,
    "log": np.log,
    "log10": np.log10,
    "exp": np.exp,
    "min": np.minimum,
    "max": np.maximum,
    "round": np.round,
}


def normalize_column_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", name.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "Derived"
    if cleaned[0].isdigit():
        cleaned = f"Col_{cleaned}"
    return cleaned


def split_formula(formula: str) -> Tuple[str, str]:
    if "=" not in formula:
        raise ValueError("Formula must use the form: NewColumn = expression")

    left, right = formula.split("=", 1)
    new_col = normalize_column_name(left)
    expression = right.strip()

    if not expression:
        raise ValueError("Formula expression is empty.")

    return new_col, expression


def validate_expression_ast(expression: str):
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Call,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Tuple,
    )

    tree = ast.parse(expression, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                raise ValueError("Only these functions are allowed: " + ", ".join(sorted(ALLOWED_FUNCS)))

    return tree


def evaluate_formula(df: pd.DataFrame, formula: str) -> Tuple[pd.DataFrame, str]:
    new_col, expression = split_formula(formula)
    validate_expression_ast(expression)

    if new_col in df.columns:
        raise ValueError(f"Column already exists: {new_col}")

    local_dict = {}
    for column in df.columns:
        safe_name = normalize_column_name(str(column))
        values = pd.to_numeric(df[column], errors="coerce")
        local_dict[safe_name] = values
        if safe_name != column and isinstance(column, str):
            local_dict[column] = values

    local_dict.update(ALLOWED_FUNCS)

    try:
        result = eval(compile(ast.parse(expression, mode="eval"), "<formula>", "eval"), {"__builtins__": {}}, local_dict)
    except NameError as exc:
        raise ValueError(
            "Unknown column or function in formula. Use sanitized column names shown in the helper table."
        ) from exc

    out = df.copy()
    out[new_col] = result
    return out, new_col


def sanitized_column_map(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Original Column": list(df.columns),
            "Formula Name": [normalize_column_name(str(column)) for column in df.columns],
        }
    )
