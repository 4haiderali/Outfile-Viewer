from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass(frozen=True)
class ThresholdRule:
    name: str
    column: str
    direction: str  # "min" or "max"
    threshold: float
    required_pct: float


def check_compliance(df: pd.DataFrame, rules: List[ThresholdRule]) -> pd.DataFrame:
    results = []

    for rule in rules:
        if rule.column not in df.columns:
            results.append(
                {
                    "Rule": rule.name,
                    "Column": rule.column,
                    "Direction": rule.direction,
                    "Threshold": rule.threshold,
                    "Required Pass Rate (%)": rule.required_pct,
                    "Total Rows": 0,
                    "Passing Rows": 0,
                    "Violations": 0,
                    "Pass Rate (%)": 0.0,
                    "Worst Value": None,
                    "Status": "MISSING COLUMN",
                }
            )
            continue

        values = pd.to_numeric(df[rule.column], errors="coerce").dropna()
        total = len(values)

        if total == 0:
            pass_rate = 0.0
            passing = 0
            violations = 0
            worst_value = None
            status = "NO DATA"
        else:
            if rule.direction == "min":
                passing_mask = values >= rule.threshold
                worst_value = float(values.min())
            else:
                passing_mask = values <= rule.threshold
                worst_value = float(values.max())

            passing = int(passing_mask.sum())
            violations = int(total - passing)
            pass_rate = passing / total * 100
            status = "PASS" if pass_rate >= rule.required_pct else "FAIL"

        results.append(
            {
                "Rule": rule.name,
                "Column": rule.column,
                "Direction": rule.direction,
                "Threshold": rule.threshold,
                "Required Pass Rate (%)": rule.required_pct,
                "Total Rows": total,
                "Passing Rows": passing,
                "Violations": violations,
                "Pass Rate (%)": round(pass_rate, 3),
                "Worst Value": worst_value,
                "Status": status,
            }
        )

    return pd.DataFrame(results)


def violating_rows(df: pd.DataFrame, rule: ThresholdRule) -> pd.DataFrame:
    if rule.column not in df.columns:
        return pd.DataFrame()

    values = pd.to_numeric(df[rule.column], errors="coerce")

    if rule.direction == "min":
        mask = values < rule.threshold
    else:
        mask = values > rule.threshold

    out = df.loc[mask].copy()
    if out.empty:
        return out

    out.insert(0, "Rule", rule.name)
    out.insert(1, "Checked Column", rule.column)
    out.insert(2, "Threshold", rule.threshold)
    out.insert(3, "Direction", rule.direction)

    return out


import json
from dataclasses import asdict
from pathlib import Path


def rules_to_dicts(rules):
    return [asdict(rule) for rule in rules]


def rules_from_dicts(items):
    out = []
    for item in items:
        try:
            out.append(
                ThresholdRule(
                    name=str(item.get("name", "Rule")),
                    column=str(item.get("column", "")),
                    direction=str(item.get("direction", "min")),
                    threshold=float(item.get("threshold", 0.0)),
                    required_pct=float(item.get("required_pct", 100.0)),
                )
            )
        except Exception:
            continue
    return out


def save_rules(path, rules):
    path = Path(path)
    path.write_text(json.dumps(rules_to_dicts(rules), indent=2), encoding="utf-8")


def load_rules(path):
    path = Path(path)
    if not path.exists():
        return []
    return rules_from_dicts(json.loads(path.read_text(encoding="utf-8")))
