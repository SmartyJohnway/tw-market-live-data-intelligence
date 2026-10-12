"""A6-only durable pre-dispatch accounting for the existing H3/H2 transports."""
from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

_operation: ContextVar[tuple[int, str, str] | None] = ContextVar("a6_operation", default=None)


def attempt_2_eligible(*, outcome: str, stage_witness_available: bool) -> bool:
    """Apply the frozen continuation rule; success, terminal, and no-evidence are final."""
    return (outcome == "transient_source_failure" and not stage_witness_available) or (
        outcome == "stage_witness_unavailable" and not stage_witness_available
    )


def operation_context(attempt: int, operation: str, operation_id: str):
    class _Context:
        def __enter__(self):
            self.token = _operation.set((attempt, operation, operation_id))
        def __exit__(self, *_args):
            _operation.reset(self.token)
    return _Context()


def _paths() -> tuple[Path, Path] | None:
    value = os.environ.get("A6_SESSION_ROOT")
    if not value:
        return None
    root = Path(value).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root / "session.json", root / "transport-ledger.jsonl"


def _append(ledger: Path, event: dict) -> None:
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, line)
        os.fsync(fd)
    finally:
        os.close(fd)


def reserve_dispatch(*, method: str, url: str) -> dict | None:
    paths = _paths()
    if paths is None:
        return None
    session_path, ledger = paths
    if _operation.get() is None:
        raise RuntimeError("a6_dispatch_without_operation_context")
    attempt, operation, operation_id = _operation.get()  # type: ignore[misc]
    parts = urlsplit(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    allowed_url = (
        parts.scheme == "https" and parts.hostname == "www.twse.com.tw"
        and parts.path == "/exchangeReport/STOCK_DAY"
        and query.get("response") == ["html"]
        and query.get("stockNo") == ["2330"]
        and len(query.get("date", [])) == 1
    ) if operation == "H3" else (
        parts.scheme == "https" and parts.hostname == "openapi.twse.com.tw"
        and parts.path == "/v1/exchangeReport/TWT48U_ALL" and not parts.query
    ) if operation == "H2" else False
    if method != "GET" or not allowed_url:
        raise RuntimeError("a6_dispatch_contract_rejected")
    with session_path.open("r+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        session = json.load(stream)
        count = int(session.get("actual_dispatches", 0))
        attempt_count = int(session.get("attempt_dispatches", {}).get(str(attempt), 0))
        if (session.get("network_enabled") is not True or attempt > 2 or count >= 8
                or count >= 10 or attempt_count >= 4
                or (operation == "H3" and int(session.get("attempt_h3", {}).get(str(attempt), 0)) >= 3)
                or (operation == "H2" and int(session.get("attempt_h2", {}).get(str(attempt), 0)) >= 1)):
            raise RuntimeError("a6_dispatch_budget_exhausted")
        number = count + 1
        session["actual_dispatches"] = number
        session.setdefault("attempt_dispatches", {})[str(attempt)] = attempt_count + 1
        counter = "attempt_h3" if operation == "H3" else "attempt_h2"
        session.setdefault(counter, {})[str(attempt)] = int(session.get(counter, {}).get(str(attempt), 0)) + 1
        reservation_id = f"a6-{number:02d}-{uuid4().hex}"
        session.setdefault("reservations", []).append(reservation_id)
        stream.seek(0); stream.truncate(); json.dump(session, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
    source_id = "H3-TWSE-DEFAULT-BOUNDED" if operation == "H3" else "H2-TWSE-EXRIGHT-PRE-OPENAPI"
    _append(ledger, {"event": "reserved", "reservation_id": reservation_id, "attempt": attempt,
                     "operation": operation, "source_id": source_id, "target": "TWSE:2330",
                     "operation_id": operation_id, "method": method,
                     "url": url, "dispatch_number": number, "redirects": 0, "retries": 0,
                     "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"reservation_id": reservation_id, "attempt": attempt, "operation": operation,
            "source_id": source_id, "target": "TWSE:2330", "operation_id": operation_id,
            "dispatch_number": number, "method": method, "url": url}


def complete_dispatch(reservation: dict | None, *, status: int | None, final_url: str | None,
                      content_type: str | None, body: bytes | None, error: str | None = None) -> None:
    if reservation is None:
        return
    _, ledger = _paths() or (None, None)
    assert ledger is not None
    _append(ledger, {"event": "completed", **reservation, "status": status,
                     "final_url": final_url, "content_type": content_type,
                     "byte_count": len(body) if body is not None else None,
                     "sha256": hashlib.sha256(body).hexdigest() if body is not None else None,
                     "error": error, "redirects": 0, "retries": 0, "retry_count": 0,
                     "timestamp": datetime.now(timezone.utc).isoformat()})
