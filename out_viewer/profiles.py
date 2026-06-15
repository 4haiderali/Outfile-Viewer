"""Project template/profile helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone


PROFILE_SCHEMA = "out-viewer-profile-v1"


def build_profile_payload(
    *,
    name: str,
    unit_maps: dict | None = None,
    expression_rules: list | None = None,
    notes: dict | None = None,
    chart_defaults: dict | None = None,
) -> bytes:
    payload = {
        "schema": PROFILE_SCHEMA,
        "name": name or "Out Viewer Profile",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "unit_maps": unit_maps or {},
        "expression_rules": expression_rules or [],
        "notes": notes or {},
        "chart_defaults": chart_defaults or {},
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def read_profile_payload(data: bytes) -> dict:
    payload = json.loads(data.decode("utf-8"))
    if payload.get("schema") != PROFILE_SCHEMA:
        raise ValueError(f"Unsupported profile schema: {payload.get('schema')!r}")
    return payload
