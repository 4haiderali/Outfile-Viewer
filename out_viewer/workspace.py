"""Workspace save/restore helpers."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Dict, Tuple


WORKSPACE_SCHEMA = "out-viewer-workspace-v1"


def build_workspace_payload(file_history: Dict[str, dict], unit_maps: Dict[str, dict] | None = None) -> bytes:
    files = []
    for name, record in file_history.items():
        files.append(
            {
                "name": name,
                "size": int(record.get("size", 0)),
                "bytes_b64": base64.b64encode(record.get("bytes", b"")).decode("ascii"),
            }
        )

    payload = {
        "schema": WORKSPACE_SCHEMA,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "unit_maps": unit_maps or {},
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def read_workspace_payload(data: bytes) -> Tuple[list[dict], dict]:
    payload = json.loads(data.decode("utf-8"))
    if payload.get("schema") != WORKSPACE_SCHEMA:
        raise ValueError(f"Unsupported workspace schema: {payload.get('schema')!r}")

    files = []
    for item in payload.get("files", []):
        files.append(
            {
                "name": item["name"],
                "bytes": base64.b64decode(item["bytes_b64"]),
                "size": int(item.get("size", 0)),
            }
        )

    return files, payload.get("unit_maps", {})
