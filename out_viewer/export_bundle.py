"""ZIP bundle export helpers.

The export bundle is the canonical "Project file" for v26: it is the only
one of the three save formats (Workspace JSON, Profile JSON, Export Bundle
ZIP) that round-trips everything -- source files, unit tags, notes, and
saved expression rules. ``read_export_bundle`` is the counterpart to
``build_export_bundle`` and lets the Workspace tab restore a full session
from a previously-downloaded bundle. The lighter Workspace/Profile JSON
formats remain available for users who deliberately want a *partial*
export (e.g. sharing a rule profile without the underlying data files).
"""

from __future__ import annotations

from io import BytesIO
import json
import zipfile

import pandas as pd

from .batch import build_batch_html_report, build_batch_risk_table, build_batch_summary
from .workspace import build_workspace_payload


def _write_df(zf: zipfile.ZipFile, name: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        zf.writestr(name, "")
    else:
        zf.writestr(name, df.to_csv(index=False))


def build_export_bundle(file_history: dict, unit_maps: dict | None = None, notes: dict | None = None, rules: list | None = None) -> bytes:
    summary = build_batch_summary(file_history)
    risk = build_batch_risk_table(file_history)
    workspace = build_workspace_payload(file_history, unit_maps or {})
    batch_report = build_batch_html_report(summary, risk)

    bio = BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("workspace/out_viewer_workspace.json", workspace)
        zf.writestr("reports/batch_report.html", batch_report)
        _write_df(zf, "tables/batch_summary.csv", summary)
        _write_df(zf, "tables/batch_risk.csv", risk)
        zf.writestr("metadata/unit_maps.json", json.dumps(unit_maps or {}, indent=2))
        zf.writestr("metadata/notes.json", json.dumps(notes or {}, indent=2))
        zf.writestr("metadata/saved_expression_rules.json", json.dumps(rules or [], indent=2))

        for name, record in file_history.items():
            safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(name))
            zf.writestr(f"source_files/{safe}", record.get("bytes", b""))

    return bio.getvalue()


def read_export_bundle(data: bytes) -> dict:
    """Restore the contents of a project bundle previously written by
    :func:`build_export_bundle`.

    Returns a dict with keys ``files`` (list of ``{"name", "bytes"}``),
    ``unit_maps``, ``notes`` and ``expression_rules``. Missing pieces
    default to empty containers so older/partial bundles still load.
    """
    files: list[dict] = []
    unit_maps: dict = {}
    notes: dict = {}
    expression_rules: list = []

    with zipfile.ZipFile(BytesIO(data)) as zf:
        names = set(zf.namelist())

        for entry in names:
            if entry.startswith("source_files/") and not entry.endswith("/"):
                files.append({"name": entry.split("/", 1)[1], "bytes": zf.read(entry)})

        if "metadata/unit_maps.json" in names:
            unit_maps = json.loads(zf.read("metadata/unit_maps.json").decode("utf-8"))
        if "metadata/notes.json" in names:
            notes = json.loads(zf.read("metadata/notes.json").decode("utf-8"))
        if "metadata/saved_expression_rules.json" in names:
            expression_rules = json.loads(zf.read("metadata/saved_expression_rules.json").decode("utf-8"))

    return {
        "files": files,
        "unit_maps": unit_maps,
        "notes": notes,
        "expression_rules": expression_rules,
    }
