"""Safe-ish expression rules for compliance checks.

Supports expressions such as:
    Ia < 1.1
    abs(Ia - Ib) < 0.05
    (Ia < 1.1) & (Ib < 1.1)
    Energy_max <= 75

The expression is parsed with ast and evaluated against pandas Series.
"""

from __future__ import annotations

import ast
import operator
from typing import Any

import numpy as np
import pandas as pd


BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

CMP_OPS = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

BOOL_OPS = {
    ast.And: lambda a, b: a & b,
    ast.Or: lambda a, b: a | b,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
}

FUNCTIONS = {
    "abs": abs,
    "sqrt": np.sqrt,
    "log": np.log,
    "maximum": np.maximum,
    "minimum": np.minimum,
}


def _eval(node: ast.AST, df: pd.DataFrame) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, df)

    if isinstance(node, ast.Name):
        if node.id not in df.columns:
            raise ValueError(f"Unknown column: {node.id}")
        return pd.to_numeric(df[node.id], errors="coerce")

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise ValueError("Only numeric/bool constants are supported.")

    if isinstance(node, ast.UnaryOp):
        val = _eval(node.operand, df)
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.Not):
            return ~val
        raise ValueError("Unsupported unary operator.")

    if isinstance(node, ast.BinOp):
        left = _eval(node.left, df)
        right = _eval(node.right, df)
        op_type = type(node.op)
        if op_type in BIN_OPS:
            return BIN_OPS[op_type](left, right)
        if op_type in BOOL_OPS:
            return BOOL_OPS[op_type](left, right)
        raise ValueError("Unsupported binary operator.")

    if isinstance(node, ast.BoolOp):
        values = [_eval(v, df) for v in node.values]
        op_type = type(node.op)
        if op_type not in BOOL_OPS:
            raise ValueError("Unsupported boolean operator.")
        result = values[0]
        for value in values[1:]:
            result = BOOL_OPS[op_type](result, value)
        return result

    if isinstance(node, ast.Compare):
        left = _eval(node.left, df)
        result = pd.Series(True, index=df.index)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, df)
            op_type = type(op)
            if op_type not in CMP_OPS:
                raise ValueError("Unsupported comparison operator.")
            result = result & CMP_OPS[op_type](left, right)
            left = right
        return result

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            raise ValueError("Unsupported function. Allowed: " + ", ".join(FUNCTIONS))
        args = [_eval(arg, df) for arg in node.args]
        return FUNCTIONS[node.func.id](*args)

    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def evaluate_expression_rule(df: pd.DataFrame, expression: str) -> pd.Series:
    tree = ast.parse(expression, mode="eval")
    mask = _eval(tree, df)
    if isinstance(mask, (bool, np.bool_)):
        return pd.Series(bool(mask), index=df.index)
    if not isinstance(mask, pd.Series):
        raise ValueError("Expression must evaluate to a boolean Series.")
    return mask.fillna(False).astype(bool)


def expression_rule_summary(df: pd.DataFrame, expression: str) -> dict:
    passed = evaluate_expression_rule(df, expression)
    fail = ~passed
    return {
        "Expression": expression,
        "Rows": int(len(df)),
        "Passed": int(passed.sum()),
        "Failed": int(fail.sum()),
        "Pass %": round(float(passed.mean() * 100), 3) if len(df) else 0.0,
    }


def expression_rule_failures(df: pd.DataFrame, expression: str) -> pd.DataFrame:
    passed = evaluate_expression_rule(df, expression)
    out = df.loc[~passed].copy()
    out.insert(0, "Rule Expression", expression)
    return out
