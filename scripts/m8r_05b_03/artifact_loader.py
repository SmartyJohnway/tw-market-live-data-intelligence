"""Strict local JSON input loader; this layer never fetches artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from .errors import OrchestrationError


def load_json_object(path: str | Path) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestrationError("artifact_load_invalid") from exc
    if not isinstance(value, dict):
        raise OrchestrationError("artifact_load_invalid")
    return value
