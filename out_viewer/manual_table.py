"""Manual table extraction tools for parser edge cases."""

from __future__ import annotations

from io import StringIO

import pandas as pd


def line_window(lines: list[str], start_line: int, end_line: int) -> list[str]:
    start = max(1, int(start_line))
    end = min(len(lines), int(end_line))
    if end < start:
        return []
    return lines[start - 1:end]


def parse_manual_table(lines: list[str], start_line: int, end_line: int, *, header_line: int | None = None) -> pd.DataFrame:
    window = line_window(lines, start_line, end_line)
    if not window:
        return pd.DataFrame()

    if header_line is not None:
        rel_header = int(header_line) - int(start_line)
        if 0 <= rel_header < len(window):
            header = window[rel_header]
            data_lines = window[rel_header + 1:]
            text = "\n".join([header] + data_lines)
            return pd.read_csv(StringIO(text), sep=r"\s+", engine="python")

    text = "\n".join(window)
    return pd.read_csv(StringIO(text), sep=r"\s+", engine="python", header=None)


def preview_lines(lines: list[str], start_line: int, end_line: int) -> pd.DataFrame:
    rows = []
    for idx, text in enumerate(line_window(lines, start_line, end_line), start=max(1, int(start_line))):
        rows.append({"Line": idx, "Text": text})
    return pd.DataFrame(rows)
