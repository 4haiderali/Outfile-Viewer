"""Selectable HTML report builder with embedded Plotly snippets.

Built on top of :mod:`out_viewer.html_report`, the same engine used by the
enhanced Cockpit report and the Batch report, so all three exported reports
share one stylesheet and one set of table/list/figure renderers.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .html_report import render_document, render_figures, render_table


def build_sectioned_report(
    *,
    title: str,
    sections: dict[str, str],
    notes: pd.DataFrame | None = None,
    embedded_figures: Iterable[str] | None = None,
) -> bytes:
    body_sections = [("Notes / Annotations", render_table(notes, "No notes were added."))]
    for name, content in sections.items():
        body_sections.append((name, content))
    body_sections.append(("Embedded Figures", render_figures(embedded_figures)))
    return render_document(title=title, body_sections=body_sections)


def df_section(df: pd.DataFrame, limit: int = 50) -> str:
    return render_table(df.head(limit) if df is not None and not df.empty else df)
