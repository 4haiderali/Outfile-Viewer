"""Column unit helpers."""

from __future__ import annotations

from typing import Dict, Iterable

import pandas as pd


_UNIT_HINTS = [
    ("voltage", "pu"),
    ("volt", "V"),
    ("current", "A"),
    ("curr", "A"),
    ("power", "MW"),
    ("mw", "MW"),
    ("mvar", "MVAr"),
    ("freq", "Hz"),
    ("frequency", "Hz"),
    ("angle", "deg"),
    ("energy", "kJ"),
    ("time", "s"),
]


def infer_unit(column: object) -> str:
    name = str(column).strip()
    low = name.lower()

    # Explicit unit in a header like "Voltage (pu)" or "Current[kA]".
    for left, right in [("(", ")"), ("[", "]")]:
        if left in name and right in name:
            try:
                inside = name.split(left, 1)[1].split(right, 1)[0].strip()
                if inside:
                    return inside
            except Exception:
                pass

    for token, unit in _UNIT_HINTS:
        if token in low:
            return unit

    if low in {"v", "va", "vb", "vc"} or low.startswith(("v_", "volt_", "e")):
        return "pu"
    if low in {"ia", "ib", "ic"} or low.startswith(("i_", "curr_")):
        return "A"

    return ""


def unit_state_key(file_label: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(file_label))
    return f"unit_map_{safe}"


def default_unit_map(columns: Iterable[object]) -> Dict[str, str]:
    return {str(column): infer_unit(column) for column in columns}


def unit_table(columns: Iterable[object], unit_map: Dict[str, str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        col = str(column)
        rows.append(
            {
                "Column": col,
                "Unit": unit_map.get(col, infer_unit(col)),
                "Inferred Unit": infer_unit(col),
            }
        )
    return pd.DataFrame(rows)


def stats_with_units(stats: pd.DataFrame, unit_map: Dict[str, str] | None) -> pd.DataFrame:
    if stats.empty or not unit_map or "Column" not in stats.columns:
        return stats.copy()

    out = stats.copy()
    out.insert(1, "Unit", out["Column"].astype(str).map(lambda col: unit_map.get(col, "")))
    return out


def column_label(column: object, unit_map: Dict[str, str] | None) -> str:
    col = str(column)
    unit = unit_map.get(col, "") if unit_map else ""
    return f"{col} ({unit})" if unit else col
