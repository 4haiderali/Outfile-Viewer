"""Shared per-request context passed to every tab's ``render(ctx)`` function.

Before v26 every tab in ``app.py`` re-derived the same handful of values
(``current_name``, ``stem``, ``primary_table``, ``unit_map``, ...) from
``st.session_state`` and local variables. Bundling them into one dataclass,
built once in ``app.py``, means tab modules take a single argument and
cannot accidentally read a stale or differently-scoped copy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .parser import DetectedTable


@dataclass
class AppContext:
    current_name: str
    record: dict
    parsed: dict
    tables: list[DetectedTable]
    metadata_df: pd.DataFrame
    stats_df: pd.DataFrame
    main_table_list: list[DetectedTable]
    pdf_table_list: list[DetectedTable]
    primary_table: DetectedTable | None
    diagnostics: dict
    stem: str
    unit_key: str
    unit_map: dict
    file_history: dict = field(default_factory=dict)

    @property
    def file_count(self) -> int:
        return len(self.file_history)

    @property
    def file_bytes(self) -> bytes:
        return self.record.get("bytes", b"")
