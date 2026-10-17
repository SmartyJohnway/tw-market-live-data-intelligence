"""Deterministic resource admission shared by the Local Service write surfaces."""
from __future__ import annotations

import os
import shutil
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from starlette.responses import JSONResponse


MAX_RESOURCE_INTENSIVE_CONCURRENCY = 1
RESOURCE_CONCURRENCY_REASON = "resource_concurrency_limit"
RESOURCE_DISK_REASON = "resource_disk_admission_failed"
RESOURCE_DISK_UNAVAILABLE_REASON = "resource_disk_admission_unavailable"

LIGHT_READ = "LIGHT_READ"
BOUNDED_OFFLINE_PLANNING = "BOUNDED_OFFLINE_PLANNING"
PERSISTENT_MUTATION = "PERSISTENT_MUTATION"
RESOURCE_INTENSIVE_ACTION = "RESOURCE_INTENSIVE_ACTION"
RESOURCE_INTENSIVE_PROJECTION = "RESOURCE_INTENSIVE_PROJECTION"


def classify_request(method: str, path: str) -> str:
    """Classify active Local Service routes without relying on request content."""
    method = method.upper()
    if method == "POST" and path in {
        "/api/unified/authorizations",
        "/api/unified/executions",
        "/api/unified/fetch-evidence",
        "/api/unified/result-package",
    }:
        return RESOURCE_INTENSIVE_ACTION
    if method == "GET" and path.startswith("/api/unified/result-package/") and (
        path.endswith("/audit.json") or path.endswith("/handoff")
    ):
        return RESOURCE_INTENSIVE_PROJECTION
    if method == "POST" and path in {
        "/api/watchlist-mutations/preview",
        "/api/watchlist-mutations/commit",
        "/api/evidence-request-previews",
    }:
        return PERSISTENT_MUTATION
    if method == "POST" and path.startswith("/api/watchlists/") and path.endswith("/evidence-request-preview"):
        return PERSISTENT_MUTATION
    if method == "POST" and path in {
        "/api/unified/validate-request",
        "/api/unified/preview-request",
        "/api/m5k/conversation/handoff",
        "/api/m5k/live-observation/plan",
        "/api/m5k/watchlist/validate",
    }:
        return BOUNDED_OFFLINE_PLANNING
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        # Unknown write verbs/routes fail into the bounded admission class so
        # a newly retained write endpoint cannot bypass the ceiling silently.
        return PERSISTENT_MUTATION
    return LIGHT_READ


class ResourceAdmissionGate:
    """Single-process, fail-fast admission; there is no wait queue."""

    def __init__(self, limit: int = MAX_RESOURCE_INTENSIVE_CONCURRENCY) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("resource_concurrency_limit_invalid")
        self.limit = limit
        self._lock = threading.Lock()
        self._active = 0

    def try_enter(self) -> bool:
        with self._lock:
            if self._active >= self.limit:
                return False
            self._active += 1
            return True

    def leave(self) -> None:
        with self._lock:
            if self._active <= 0:
                raise RuntimeError("resource_admission_release_without_acquire")
            self._active -= 1

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    @contextmanager
    def admitted(self) -> Iterator[bool]:
        acquired = self.try_enter()
        try:
            yield acquired
        finally:
            if acquired:
                self.leave()


RESOURCE_INTENSIVE_GATE = ResourceAdmissionGate()


class ResourceAdmissionMiddleware:
    """Fail-fast gate for expensive/mutating routes across the FastAPI app."""

    def __init__(self, app, *, gate: ResourceAdmissionGate = RESOURCE_INTENSIVE_GATE):
        self.app = app
        self.gate = gate

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        resource_class = classify_request(method, path)
        if resource_class not in {
            PERSISTENT_MUTATION,
            RESOURCE_INTENSIVE_ACTION,
            RESOURCE_INTENSIVE_PROJECTION,
            BOUNDED_OFFLINE_PLANNING,
        }:
            await self.app(scope, receive, send)
            return
        if not self.gate.try_enter():
            response = JSONResponse(
                status_code=503,
                content={"error": RESOURCE_CONCURRENCY_REASON},
            )
            await response(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        finally:
            self.gate.leave()


class ResourceDiskAdmissionError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _existing_directory(path: str | os.PathLike[str]) -> Path:
    candidate = Path(path).expanduser()
    if candidate.exists() and candidate.is_file():
        candidate = candidate.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    if not candidate.exists() or not candidate.is_dir():
        raise OSError("disk_admission_root_unavailable")
    return candidate


def available_disk_bytes(path: str | os.PathLike[str]) -> int:
    """Return filesystem free bytes for the nearest existing directory."""
    try:
        return int(shutil.disk_usage(_existing_directory(path)).free)
    except (OSError, ValueError, TypeError) as exc:
        raise ResourceDiskAdmissionError(RESOURCE_DISK_UNAVAILABLE_REASON) from exc


def require_disk_capacity(path: str | os.PathLike[str], required_bytes: int) -> int:
    """Fail closed when a persistent operation cannot observe or fit its write."""
    if isinstance(required_bytes, bool) or not isinstance(required_bytes, int) or required_bytes < 0:
        raise ValueError("resource_disk_requirement_invalid")
    free = available_disk_bytes(path)
    if free < required_bytes:
        raise ResourceDiskAdmissionError(RESOURCE_DISK_REASON)
    return free


def sqlite_write_requirement(database_path: str | os.PathLike[str], serialized_growth_bytes: int) -> int:
    """Dynamic SQLite admission: existing DB plus payload and rollback coexistence.

    The estimate reserves one current-database-sized rollback-journal allowance
    and the serialized new content in both the journal/growth envelope. SQLite
    transactions remain atomic; a filesystem failure after admission still
    causes the existing transaction to roll back.
    """
    if isinstance(serialized_growth_bytes, bool) or not isinstance(serialized_growth_bytes, int) or serialized_growth_bytes < 0:
        raise ValueError("resource_disk_requirement_invalid")
    try:
        size = Path(database_path).stat().st_size
    except FileNotFoundError:
        size = 0
    except OSError as exc:
        raise ResourceDiskAdmissionError(RESOURCE_DISK_UNAVAILABLE_REASON) from exc
    return 2 * (size + serialized_growth_bytes)


def serialized_json_bytes(value: object, *, indent: int | None = None) -> int:
    import json

    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=indent)
    if os.linesep == "\r\n":
        text = text.replace("\n", "\r\n")
    return len(text.encode("utf-8"))


def serialized_text_bytes(value: str) -> int:
    if not isinstance(value, str):
        raise ValueError("resource_text_payload_invalid")
    if os.linesep == "\r\n":
        value = value.replace("\n", "\r\n")
    return len(value.encode("utf-8"))
