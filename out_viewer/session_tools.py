"""Session/cache helpers."""

from __future__ import annotations

import pandas as pd


def session_inventory(session_state) -> pd.DataFrame:
    rows = []
    for key, value in session_state.items():
        type_name = type(value).__name__
        size_hint = ""
        if isinstance(value, dict):
            size_hint = f"{len(value)} item(s)"
        elif isinstance(value, list):
            size_hint = f"{len(value)} item(s)"
        elif hasattr(value, "shape"):
            size_hint = str(getattr(value, "shape"))
        rows.append({"Key": str(key), "Type": type_name, "Size / Shape": size_hint})
    return pd.DataFrame(rows).sort_values("Key")


def reset_analysis_state(session_state, *, keep_files: bool = True) -> None:
    keep = {"file_history"} if keep_files else set()
    for key in list(session_state.keys()):
        if key not in keep:
            del session_state[key]
    if keep_files and "file_history" not in session_state:
        session_state["file_history"] = {}
