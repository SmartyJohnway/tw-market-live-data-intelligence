"""Small typed result contracts owned by the M8R-05B-03 layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperationResult:
    operation_id: str
    status: str
    executor_id: str
    expected_evidence_contract: str
    evidence: dict[str, Any] | None
    omission_reason: str | None
