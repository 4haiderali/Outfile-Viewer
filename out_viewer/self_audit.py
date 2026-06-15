"""Self-audit helpers for project health and maintainability."""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd


def audit_python_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    return {
        "File": str(path),
        "Lines": len(text.splitlines()),
        "Functions": len(functions),
        "Classes": len(classes),
        "Imports": len(imports),
        "Largest Function Count Note": "Split recommended" if len(text.splitlines()) > 800 else "OK",
    }


def audit_project(root: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rows.append(audit_python_file(path))
    return pd.DataFrame(rows)


def architecture_issues(audit_df: pd.DataFrame) -> list[str]:
    """Findings that depend on the actual audit data -- i.e. things that
    might or might not be true depending on the current codebase size."""
    issues = []
    if audit_df.empty:
        return ["No Python files found."]

    large = audit_df[audit_df["Lines"] > 800]
    if not large.empty:
        names = ", ".join(Path(p).name for p in large["File"])
        issues.append(f"These files exceed 800 lines and are candidates to split into smaller modules: {names}.")
    if audit_df["Lines"].sum() > 2500:
        issues.append(
            f"Total project size is {int(audit_df['Lines'].sum()):,} lines. "
            "Keep business logic in `out_viewer/` modules and limit `app.py` to orchestration."
        )
    if (audit_df["Functions"] == 0).any():
        issues.append("Some files define no functions; that's fine for config/constants, but they should stay small.")
    return issues


def general_reminders() -> list[str]:
    """Reminders that are always true regardless of the current audit --
    shown separately from :func:`architecture_issues` so the UI can
    distinguish "something to fix" from "good habits to keep up"."""
    return [
        "Run the included pytest suite after each feature build.",
        "Use stable install verification before accepting a release.",
    ]


def source_metrics_text(root: Path) -> bytes:
    audit = audit_project(root)
    lines = []
    lines.append("# Out Viewer Source Audit")
    lines.append("")
    lines.append(f"Python files: {len(audit)}")
    lines.append(f"Total Python lines: {int(audit['Lines'].sum()) if not audit.empty else 0}")
    lines.append("")
    lines.append("## Findings")
    issues = architecture_issues(audit)
    if issues:
        for item in issues:
            lines.append(f"- {item}")
    else:
        lines.append("- None. All files are within the configured size thresholds.")
    lines.append("")
    lines.append("## General Reminders")
    for item in general_reminders():
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Files")
    if not audit.empty:
        for _, row in audit.iterrows():
            lines.append(f"- {row['File']}: {row['Lines']} lines, {row['Functions']} functions, {row['Classes']} classes")
    return "\n".join(lines).encode("utf-8")
