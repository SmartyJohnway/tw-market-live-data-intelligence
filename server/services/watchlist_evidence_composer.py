"""Offline Watchlist-to-Unified-Request composition with bounded provenance."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import jsonschema

from scripts.m8r_09_persistent_watchlists import (
    DEFAULT_ROOT,
    PersistentWatchlistStore,
    WatchlistError,
    canonical_json,
)
from server.services.unified_mode_a import validate_mode_a_request


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "docs" / "contracts" / "schemas"
REQUEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "unified_market_evidence_request.v1.schema.json"
CATALOG_PATH = REPO_ROOT / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v1.json"
SELECTION_DIRECTORY = "evidence_selections"


class WatchlistEvidenceCompositionError(Exception):
    def __init__(self, code: str, details: dict[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__(code)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def _validate(value: Any, schema_name: str) -> None:
    schema = _load_schema(schema_name)
    errors = sorted(
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        raise WatchlistEvidenceCompositionError(
            "WATCHLIST_SELECTION_SCHEMA_INVALID",
            {"schema": schema_name, "message": errors[0].message},
        )


def _request_hash(request: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(request).encode("utf-8")).hexdigest()


def _selection_hash(selection: dict[str, Any]) -> str:
    value = copy.deepcopy(selection)
    value.pop("content_sha256", None)
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _catalog_bounds() -> dict[str, int]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    bounds = catalog.get("bounds", {})
    return {
        "default_target_limit": int(bounds["default_target_limit"]),
        "hard_target_limit": int(bounds["hard_target_limit"]),
        "default_operation_limit": int(bounds["default_operation_limit"]),
        "hard_operation_limit": int(bounds["hard_operation_limit"]),
    }


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class WatchlistEvidenceComposer:
    """Compose an immutable request from a verified watchlist revision."""

    def __init__(
        self,
        *,
        store: PersistentWatchlistStore,
        request_validator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        now: Callable[[], str] = _utc_now,
    ):
        self.store = store
        self.request_validator = request_validator or validate_mode_a_request
        self.now = now

    def _resolved_target(
        self,
        service: Any,
        *,
        query: str,
        market_hint: str | None,
        source: str,
        client_reference: str,
        entry_id: str | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        resolution = service.resolve(query, market_hint=market_hint)
        temporary = {
            "input": query,
            "market_hint": market_hint,
            "resolution_status": resolution.status,
            "instrument_id": None,
            "canonical_target_id": None,
        }
        if resolution.status != "resolved":
            detail: dict[str, Any] = {
                "code": "IDENTITY_AMBIGUOUS" if resolution.status == "ambiguous" else "IDENTITY_NOT_FOUND",
                "input": query,
                "market_hint": market_hint,
            }
            if resolution.status == "ambiguous":
                detail["candidates"] = [service.describe(record) for record in resolution.candidates]
            return None, temporary | {"blocker": detail}
        description = service.describe(resolution.selected)
        instrument = description.get("instrument_id")
        market = description.get("market")
        if not isinstance(instrument, str) or market not in {"TWSE", "TPEX", "TAIFEX"}:
            return None, temporary | {"blocker": {"code": "IDENTITY_SCHEME_UNSUPPORTED", "input": query}}
        temporary.update(
            instrument_id=instrument,
            canonical_target_id=description.get("canonical_target_id"),
        )
        selected = {
            "source": source,
            "watchlist_entry_id": entry_id,
            "temporary_input": query if source == "temporary" else None,
            "instrument_id": instrument,
            "canonical_target_id": description["canonical_target_id"],
            "market": market,
            "security_code": description["security_code"],
            "client_target_reference": client_reference,
        }
        return selected, temporary

    def compose(self, payload: dict[str, Any], *, watchlist_id: str | None = None) -> dict[str, Any]:
        _validate(payload, "watchlist_evidence_selection_request.v1.schema.json")
        if watchlist_id is None and payload.get("expected_watchlist_version") is not None:
            raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_SCHEMA_INVALID")
        service = self.store.identity_service_for_read()
        selected: list[dict[str, Any]] = []
        temporary_results: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        deduplication: list[dict[str, Any]] = []
        watchlist_binding = None

        if watchlist_id is not None:
            expected = payload.get("expected_watchlist_version")
            if type(expected) is not int:
                raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_SCHEMA_INVALID")
            try:
                current = self.store.get_watchlist(watchlist_id)
            except WatchlistError as exc:
                raise WatchlistEvidenceCompositionError(exc.code, exc.details) from exc
            if current["current_version"] != expected:
                raise WatchlistEvidenceCompositionError(
                    "WATCHLIST_SELECTION_STALE",
                    {"expected_version": expected, "current_version": current["current_version"]},
                )
            revision = self.store.revision(watchlist_id, expected)
            requested_ids = set(payload["selected_entry_ids"])
            by_id = {entry["watchlist_entry_id"]: entry for entry in current["entries"]}
            missing_ids = sorted(requested_ids - set(by_id))
            if missing_ids:
                raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_ENTRY_NOT_FOUND", {"entry_ids": missing_ids})
            for entry in sorted(current["entries"], key=lambda value: value["display_order"]):
                if entry["watchlist_entry_id"] not in requested_ids:
                    continue
                target, detail = self._resolved_target(
                    service,
                    query=entry["instrument_id"],
                    market_hint=None,
                    source="persistent_watchlist",
                    client_reference=entry["watchlist_entry_id"],
                    entry_id=entry["watchlist_entry_id"],
                )
                if target is None:
                    blockers.append(detail["blocker"] | {"watchlist_entry_id": entry["watchlist_entry_id"]})
                else:
                    selected.append(target)
            watchlist_binding = {
                "watchlist_id": watchlist_id,
                "version": expected,
                "revision_sha256": revision["content_sha256"],
                "security_master_release_id": getattr(service, "release_id", None),
            }

        seen = {item["instrument_id"]: item for item in selected}
        for index, temporary_input in enumerate(payload["temporary_targets"]):
            reference = temporary_input.get("client_target_reference") or f"temporary_target_{index + 1}"
            target, detail = self._resolved_target(
                service,
                query=temporary_input["input"],
                market_hint=temporary_input.get("market_hint"),
                source="temporary",
                client_reference=reference,
            )
            temporary_results.append({key: value for key, value in detail.items() if key != "blocker"})
            if target is None:
                blockers.append(detail["blocker"] | {"temporary_target_index": index})
                continue
            previous = seen.get(target["instrument_id"])
            if previous is not None:
                deduplication.append({
                    "instrument_id": target["instrument_id"],
                    "kept_source": previous["source"],
                    "discarded_source": "temporary",
                    "reason": "duplicate_instrument_identity",
                })
                continue
            seen[target["instrument_id"]] = target
            selected.append(target)

        bounds = _catalog_bounds()
        operation_count = len(selected) * len(payload["data_needs"])
        if not selected:
            blockers.append({"code": "WATCHLIST_SELECTION_EMPTY"})
        if len(selected) > bounds["hard_target_limit"]:
            blockers.append({"code": "TARGET_LIMIT_EXCEEDED", "limit": bounds["hard_target_limit"]})
        if operation_count > bounds["hard_operation_limit"]:
            blockers.append({"code": "OPERATION_LIMIT_EXCEEDED", "limit": bounds["hard_operation_limit"]})
        warnings = []
        if len(selected) > bounds["default_target_limit"]:
            warnings.append("default_target_limit_exceeded")
        if operation_count > bounds["default_operation_limit"]:
            warnings.append("default_operation_limit_exceeded")
        if blockers:
            return {
                "composition_status": "blocked",
                "request": None,
                "validation": None,
                "selection_provenance": None,
                "selected_targets": selected,
                "temporary_targets": temporary_results,
                "deduplication_decisions": deduplication,
                "blockers": blockers,
                "warnings": warnings,
                "limits": bounds | {"target_count": len(selected), "operation_count": operation_count},
            }

        request = {
            "schema_version": "unified_market_evidence_request.v1",
            "request_id": f"m8r10-workbench-{uuid.uuid4()}",
            "targets": [{
                "input": item["instrument_id"],
                "market_hint": item["market"],
                "resolution_requirement": "exact",
                "client_target_reference": item["client_target_reference"],
            } for item in selected],
            "data_needs": copy.deepcopy(payload["data_needs"]),
            "execution_mode": payload["execution_mode"],
            "response_preferences": copy.deepcopy(payload["response_preferences"]),
        }
        request_schema = json.loads(REQUEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft7Validator(request_schema).iter_errors(request))
        if errors:
            raise WatchlistEvidenceCompositionError("UNIFIED_REQUEST_SCHEMA_INVALID", {"message": errors[0].message})
        request_sha = _request_hash(request)
        selection = {
            "schema_version": "watchlist_evidence_selection.v1",
            "selection_id": str(uuid.uuid4()),
            "content_sha256": "0" * 64,
            "request_id": request["request_id"],
            "request_sha256": request_sha,
            "watchlist": watchlist_binding,
            "selected_targets": selected,
            "temporary_targets": temporary_results,
            "deduplication_decisions": deduplication,
            "created_at": self.now(),
        }
        selection["content_sha256"] = _selection_hash(selection)
        _validate(selection, "watchlist_evidence_selection.v1.schema.json")
        selection_path = self.store.root / SELECTION_DIRECTORY / f"{request_sha}.json"
        if selection_path.exists():
            raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_ALREADY_EXISTS")
        validation = self.request_validator(request)
        if (
            not isinstance(validation, dict)
            or validation.get("validation_status") != "valid"
        ):
            raise WatchlistEvidenceCompositionError(
                "WATCHLIST_SELECTION_VALIDATION_FAILED",
                {
                    "validation_status": (
                        validation.get("validation_status")
                        if isinstance(validation, dict)
                        else None
                    )
                },
            )
        _atomic_write_json(selection_path, selection)
        return {
            "composition_status": "composed",
            "request": request,
            "validation": validation,
            "selection_provenance": selection,
            "selected_targets": selected,
            "temporary_targets": temporary_results,
            "deduplication_decisions": deduplication,
            "blockers": [],
            "warnings": warnings,
            "limits": bounds | {"target_count": len(selected), "operation_count": operation_count},
        }


def load_selection_provenance_for_request(
    request: dict[str, Any], *, root: Path | None = None
) -> dict[str, Any] | None:
    request_sha = _request_hash(request)
    path = (root or DEFAULT_ROOT) / SELECTION_DIRECTORY / f"{request_sha}.json"
    if not path.is_file():
        return None
    try:
        selection = json.loads(path.read_text(encoding="utf-8"))
        _validate(selection, "watchlist_evidence_selection.v1.schema.json")
    except (OSError, json.JSONDecodeError, WatchlistEvidenceCompositionError) as exc:
        raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_INTEGRITY_FAILED") from exc
    if (
        selection.get("request_id") != request.get("request_id")
        or selection.get("request_sha256") != request_sha
        or selection.get("content_sha256") != _selection_hash(selection)
    ):
        raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_INTEGRITY_FAILED")
    return selection


def validate_selection_provenance(
    selection: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    """Validate a self-contained selection sidecar against its frozen request."""
    try:
        _validate(selection, "watchlist_evidence_selection.v1.schema.json")
    except WatchlistEvidenceCompositionError as exc:
        raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_INTEGRITY_FAILED") from exc
    if (
        selection.get("request_id") != request.get("request_id")
        or selection.get("request_sha256") != _request_hash(request)
        or selection.get("content_sha256") != _selection_hash(selection)
    ):
        raise WatchlistEvidenceCompositionError("WATCHLIST_SELECTION_INTEGRITY_FAILED")
    return selection
