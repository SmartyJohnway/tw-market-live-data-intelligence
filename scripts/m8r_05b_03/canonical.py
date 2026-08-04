"""Canonical identities used by controlled execution artifacts."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def receipt_id(*, authorization_id: str, authorization_hash: str, plan_hash: str, execution_timestamp: str) -> str:
    digest = sha256_json({"authorization_id": authorization_id, "authorization_hash": authorization_hash, "plan_hash": plan_hash, "execution_timestamp": execution_timestamp})
    return "umeer-v1-" + digest[:20]
