"""Notes and annotations helpers."""

from __future__ import annotations

import pandas as pd


def notes_key(file_name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(file_name))
    return f"notes_{safe}"


def notes_to_dataframe(notes: list[dict]) -> pd.DataFrame:
    if not notes:
        return pd.DataFrame(columns=["Scope", "Target", "Note"])
    return pd.DataFrame(notes)


def add_note(notes: list[dict], *, scope: str, target: str, note: str) -> list[dict]:
    clean_note = str(note).strip()
    if not clean_note:
        return notes
    return notes + [{"Scope": scope, "Target": target, "Note": clean_note}]
