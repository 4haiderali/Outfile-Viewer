"""Batch summary helpers."""

from __future__ import annotations

import pandas as pd

from .cockpit import study_snapshot, variable_risk_ranking
from .html_report import render_document, render_table


def build_batch_summary(file_history: dict) -> pd.DataFrame:
    rows = []
    for name, record in file_history.items():
        parsed = record.get("parsed", {})
        tables = parsed.get("tables", [])
        snap = study_snapshot(parsed, tables, name)
        rows.append(
            {
                "File": name,
                "Size MB": round(record.get("size", 0) / (1024 * 1024), 3),
                "Status": snap.get("Status", ""),
                "Lines": snap.get("Lines", 0),
                "Main Tables": snap.get("Main Tables", 0),
                "PDF Tables": snap.get("PDF Tables", 0),
                "Primary Rows": snap.get("Primary Rows", 0),
                "Primary Columns": snap.get("Primary Columns", 0),
                "Highest Risk Variable": snap.get("Highest Risk Variable", ""),
                "Risk Score": snap.get("Risk Score", ""),
            }
        )
    return pd.DataFrame(rows)


def build_batch_risk_table(file_history: dict, top_n: int = 5) -> pd.DataFrame:
    rows = []
    for name, record in file_history.items():
        parsed = record.get("parsed", {})
        tables = parsed.get("tables", [])
        main_tables = [table for table in tables if getattr(table, "kind", "") == "main"]
        if not main_tables:
            continue
        primary = max(main_tables, key=lambda table: len(table.data))
        risk = variable_risk_ranking(primary.data)
        if risk.empty:
            continue
        for rank, (_, row) in enumerate(risk.head(top_n).iterrows(), start=1):
            rows.append({"File": name, "Rank": rank, **row.to_dict()})
    return pd.DataFrame(rows)


def build_batch_html_report(summary: pd.DataFrame, risk: pd.DataFrame) -> bytes:
    sections = [
        ("Batch Summary", render_table(summary, "No files loaded.")),
        ("Top Risk Variables by File", render_table(risk, "No risk data available.")),
    ]
    return render_document(
        title="Out Viewer Batch Report",
        heading=".out Output Viewer Batch Report",
        body_sections=sections,
    )
