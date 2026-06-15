from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .constants import INDEX_NAMES
from .html_report import render_cards, render_document, render_list, render_note, render_table
from .units import stats_with_units, unit_table


def numeric_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def non_index_numeric_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in numeric_columns(df) if str(c).lower() not in INDEX_NAMES]


def detect_run_column(df: pd.DataFrame):
    nums = numeric_columns(df)
    for c in df.columns:
        if str(c).lower() in INDEX_NAMES and c in nums:
            return c
    return nums[0] if nums else None



def _relative_scale(mean: float, median: float, max_abs: float) -> float:
    candidates = [abs(median), abs(mean), max_abs]
    candidates = [value for value in candidates if value and not math.isnan(value)]
    return max(candidates) if candidates else np.nan


def _robust_zscores(s: pd.Series) -> pd.Series:
    median = float(s.median())
    mad = float((s - median).abs().median())

    if mad > 0:
        return 0.6745 * (s - median) / mad

    q1, q3 = np.percentile(s, [25, 75])
    iqr = float(q3 - q1)
    if iqr > 0:
        return (s - median) / (iqr / 1.349)

    return pd.Series(0.0, index=s.index)


def extended_statistics(df: pd.DataFrame) -> pd.DataFrame:
    cols = numeric_columns(df)
    if not cols:
        return pd.DataFrame()

    nd = df[cols].apply(pd.to_numeric, errors="coerce")
    rows = []
    run_col = detect_run_column(df)

    for col in cols:
        s = nd[col].dropna()
        if s.empty:
            continue

        min_val = float(s.min())
        max_val = float(s.max())
        mean = float(s.mean())
        std = float(s.std()) if len(s) > 1 else 0.0
        median = float(s.median())
        max_abs = float(s.abs().max())
        raw_range = max_val - min_val
        scale = _relative_scale(mean, median, max_abs)
        rel_range_pct = raw_range / scale * 100 if scale and not math.isnan(scale) else np.nan

        q = np.percentile(s, [1, 2, 5, 10, 25, 50, 75, 90, 95, 98, 99])

        if abs(mean) > 1e-12:
            cv = std / abs(mean) * 100
            cv_status = "OK"
        else:
            cv = np.nan
            cv_status = "Mean near zero; CV not meaningful"

        mean_sigma_outliers = int(((s - mean).abs() > 2 * std).sum()) if std and not math.isnan(std) else 0
        robust_z = _robust_zscores(s)
        robust_max_z = float(robust_z.abs().max()) if not robust_z.empty else 0.0
        robust_outlier_count = int((robust_z.abs() > 3.5).sum()) if not robust_z.empty else 0

        min_run = None
        max_run = None
        if run_col is not None and run_col in df.columns:
            try:
                min_run = df.loc[s.idxmin(), run_col]
                max_run = df.loc[s.idxmax(), run_col]
            except Exception:
                pass

        rows.append(
            {
                "Column": col,
                "Count": int(s.count()),
                "Mean": mean,
                "Median": median,
                "Std Dev": std,
                "CV %": cv,
                "CV Status": cv_status,
                "Min": min_val,
                "Min Run": min_run,
                "P01": q[0],
                "P02": q[1],
                "P05": q[2],
                "P10": q[3],
                "P25": q[4],
                "P50": q[5],
                "P75": q[6],
                "P90": q[7],
                "P95": q[8],
                "P98": q[9],
                "P99": q[10],
                "Max": max_val,
                "Max Run": max_run,
                "Range": raw_range,
                "Relative Range %": rel_range_pct,
                "Outlier Count ±2σ": mean_sigma_outliers,
                "Robust Max Z": robust_max_z,
                "Robust Outlier Count": robust_outlier_count,
            }
        )

    return pd.DataFrame(rows).round(6)


def variable_risk_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unitless risk ranking.

    Raw range is unit-biased, so this score uses relative range, CV%,
    robust max z-score, and robust outlier count.
    """
    stats = extended_statistics(df)
    if stats.empty:
        return stats

    out = stats.copy()
    out = out[~out["Column"].astype(str).str.lower().isin(INDEX_NAMES)].copy()
    if out.empty:
        return out

    score_sources = {
        "Relative Range %": 0.40,
        "CV %": 0.25,
        "Robust Max Z": 0.20,
        "Robust Outlier Count": 0.15,
    }

    score = pd.Series(0.0, index=out.index)

    for col, weight in score_sources.items():
        vals = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0)
        maxv = vals.max()
        normalized = vals / maxv if maxv else 0
        out[f"{col} Score"] = normalized
        score += weight * normalized

    out["Risk Score"] = score * 100

    ordered_cols = [
        "Column",
        "Risk Score",
        "Relative Range %",
        "CV %",
        "CV Status",
        "Robust Max Z",
        "Robust Outlier Count",
        "Range",
        "Min",
        "Max",
        "Min Run",
        "Max Run",
    ]

    return out.sort_values("Risk Score", ascending=False)[ordered_cols].round(3)


def study_snapshot(parsed: dict, tables: list, filename: str) -> Dict[str, object]:
    main_tables = [t for t in tables if getattr(t, "kind", "") == "main"]
    pdf_tables = [t for t in tables if getattr(t, "kind", "") == "probability"]
    primary = max(main_tables, key=lambda t: len(t.data)) if main_tables else None

    snapshot = {
        "File": filename,
        "Lines": len(parsed.get("lines", [])),
        "Summary Lines": len(parsed.get("metadata", [])),
        "Metric Lines": len(parsed.get("stats", [])),
        "Main Tables": len(main_tables),
        "PDF Tables": len(pdf_tables),
        "Primary Rows": len(primary.data) if primary else 0,
        "Primary Columns": len(primary.columns) if primary else 0,
        "Status": "Parsed OK" if tables or len(parsed.get("metadata", [])) else "Text only / partial parse",
    }

    if primary is not None:
        risk = variable_risk_ranking(primary.data)
        if not risk.empty:
            snapshot["Highest Risk Variable"] = risk.iloc[0]["Column"]
            snapshot["Risk Score"] = risk.iloc[0]["Risk Score"]

    return snapshot


def recommended_next_steps(parsed: dict, tables: list, file_count: int) -> List[str]:
    steps = []
    main_tables = [t for t in tables if getattr(t, "kind", "") == "main"]
    pdf_tables = [t for t in tables if getattr(t, "kind", "") == "probability"]

    if main_tables:
        steps.append("Open Tables & Export to inspect the primary numeric table.")
        steps.append("Open Analysis to view risk ranking, percentiles, outliers, and charts.")
    else:
        steps.append("Open Raw text and Diagnostics because no main numeric table was detected.")

    if pdf_tables:
        steps.append("Open PDF to inspect probability density / cumulative probability tables.")

    if file_count >= 2:
        steps.append("Open Compare to review deltas between files.")
    else:
        steps.append("Upload a second file to enable Compare mode.")

    steps.append("Use Compliance to add pass/fail engineering thresholds.")
    steps.append("Use Report & Raw to export a technical HTML summary.")

    return steps


def explain_dataset(parsed: dict, tables: list, filename: str, file_count: int) -> str:
    snap = study_snapshot(parsed, tables, filename)
    lines = [
        f"This file is **{filename}** and contains **{snap['Lines']:,} text lines**.",
        f"The parser detected **{snap['Main Tables']} main numeric table(s)** and **{snap['PDF Tables']} probability table(s)**.",
        f"The largest primary table has **{snap['Primary Rows']:,} rows** and **{snap['Primary Columns']:,} columns**.",
    ]

    if "Highest Risk Variable" in snap:
        lines.append(
            f"The variable with the highest risk/variability score is **{snap['Highest Risk Variable']}** "
            f"(unitless score {snap['Risk Score']:.1f})."
        )

    if file_count < 2:
        lines.append("Comparison mode needs at least two uploaded files.")

    return " ".join(lines)


def compliance_templates(numeric_cols: List[str]) -> pd.DataFrame:
    rows = []
    for col in numeric_cols:
        lower = "voltage" in str(col).lower() or str(col).lower().startswith(("v", "e"))
        rows.append(
            {
                "Template": f"{col} minimum bound" if lower else f"{col} maximum bound",
                "Column": col,
                "Rule Type": "Minimum allowed" if lower else "Maximum allowed",
                "Suggested Threshold": 0.90 if lower else 1.00,
                "Required Pass %": 100.0,
            }
        )
    return pd.DataFrame(rows)


def formula_templates(numeric_cols: List[str]) -> pd.DataFrame:
    rows = []
    if len(numeric_cols) >= 3:
        a, b, c = numeric_cols[:3]
        rows.append({"Name": "Total first 3 variables", "Formula": f"{a}_{b}_{c}_total = {a} + {b} + {c}"})
        rows.append({"Name": "Spread first 3 variables", "Formula": f"{a}_{b}_{c}_spread = max({a}, max({b}, {c})) - min({a}, min({b}, {c}))"})
    if numeric_cols:
        a = numeric_cols[0]
        rows.append({"Name": "Percent of first variable", "Formula": f"{a}_pct = {a} * 100"})
        rows.append({"Name": "Squared first variable", "Formula": f"{a}_squared = {a} ** 2"})
    return pd.DataFrame(rows)


def build_enhanced_html_report(filename: str, parsed: dict, tables: list, unit_map: dict | None = None, file_count: int = 1, findings: list[str] | None = None) -> bytes:
    snap = study_snapshot(parsed, tables, filename)
    main_tables = [t for t in tables if getattr(t, "kind", "") == "main"]
    primary = max(main_tables, key=lambda t: len(t.data)) if main_tables else None

    stats_df = pd.DataFrame()
    risk_df = pd.DataFrame()
    preview_df = pd.DataFrame()

    if primary is not None:
        stats_df = stats_with_units(extended_statistics(primary.data), unit_map).head(25)
        risk_df = variable_risk_ranking(primary.data).head(15)
        preview_df = primary.data.head(20)

    meta = parsed.get("metadata", pd.DataFrame())
    units_df = unit_table(unit_map.keys(), unit_map) if unit_map else pd.DataFrame()

    sections = [
        ("", render_note(explain_dataset(parsed, tables, filename, file_count))),
        ("Executive Findings", render_list(findings, "No narrative findings were generated.")),
        (
            "Study Snapshot",
            render_cards(
                [
                    ("Lines", f"{snap['Lines']:,}"),
                    ("Main Tables", snap["Main Tables"]),
                    ("PDF Tables", snap["PDF Tables"]),
                    ("Status", snap["Status"]),
                ]
            ),
        ),
        ("Metadata / Summary", render_table(meta.head(50), "No summary metadata detected.")),
        ("Column Units", render_table(units_df, "No column units were tagged.")),
        ("Variable Risk Ranking", render_table(risk_df, "No primary table available.")),
        ("Extended Statistics", render_table(stats_df, "No numeric statistics available.")),
        ("Primary Table Preview", render_table(preview_df, "No primary table available.")),
    ]
    return render_document(
        title=f"Out Viewer Report - {filename}",
        heading=".out Output Viewer Report",
        body_sections=sections,
    )
