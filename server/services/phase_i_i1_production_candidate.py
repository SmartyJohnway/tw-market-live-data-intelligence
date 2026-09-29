"""Dormant production-capable Phase I1 source/executor candidate.

The candidate is deliberately not installed in the normal M8R-06-03 runtime
registry.  It can only be invoked through its explicitly-built candidate
registry, and still requires an already-approved 05B execution request.
Transport and selection are kept separate from the frozen pure normalizers.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    RuntimeAdapterRegistration,
    RuntimeAdapterRegistry,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_06_03_production_adapter import _require_approved_execution
from scripts.m8r_05c.citation_builder import _build_citation_id
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.twse_trading_calendar import parse_twse_roc_date
from server.services.phase_i_market_state_adapters import (
    MarketStateNormalizationError,
    normalize_tpex_market_state,
    normalize_twse_market_state,
)


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_ID = "phase_i_i1_market_state_executor"
CAPABILITY_ID = "market_state_context"
EVIDENCE_CONTRACT = "market_state_context_evidence.v1"
RESULT_SCHEMA = "unified_market_evidence_operation_result.v1"
TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 65536
MAX_BATCH_TARGETS = 500
OUTPUT_POLICY = "contained_artifact_only"
CANDIDATE_METADATA_PATH = ROOT / "config" / "phase_i_i1_production_executor_candidate.json"

SOURCE_DESCRIPTORS: dict[str, dict[str, str]] = {
    "I1-TWSE-FMTQIK-OPENAPI": {
        "market": "TWSE",
        "source_family": "TWSE_EXCHANGE_REPORT_FMTQIK",
        "source_contract_id": "TWSE_FMTQIK_OPENAPI_V1",
        "url": "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
        "role": "benchmark_and_turnover",
    },
    "I1-TWSE-BREADTH-TWTAZU-OPENAPI": {
        "market": "TWSE",
        "source_family": "TWSE_OPENDATA_TWTAZU",
        "source_contract_id": "TWSE_TWTAZU_OD_OPENAPI_V1",
        "url": "https://openapi.twse.com.tw/v1/opendata/twtazu_od",
        "role": "market_breadth",
    },
    "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI": {
        "market": "TPEX",
        "source_family": "TPEX_MAINBOARD_MARKET_HIGHLIGHT",
        "source_contract_id": "TPEX_MAINBORAD_HIGHLIGHT_OPENAPI_V1",
        "url": "https://www.tpex.org.tw/openapi/v1/tpex_mainborad_highlight",
        "role": "benchmark_breadth_and_turnover",
    },
}


class I1ProductionSourceError(ValueError):
    """A bounded source response or deterministic row selection failed."""


@dataclass(frozen=True)
class TransportObservation:
    source_id: str
    status: str
    endpoint: str
    retrieved_at: str
    http_status: int | None
    content_type: str | None
    response_byte_count: int
    response_sha256: str | None
    rows: tuple[Mapping[str, Any], ...] = ()
    error_code: str | None = None


TransportCallable = Callable[[str, int], tuple[int, Mapping[str, str], bytes]]


def _no_redirect_opener() -> urllib.request.OpenerDirector:
    class RejectRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return urllib.request.build_opener(RejectRedirect())


def _http_transport(url: str, timeout_seconds: int) -> tuple[int, Mapping[str, str], bytes]:
    """Fetch only an internally selected fixed URL, with redirects disabled."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "tw-market-live-data-intelligence/1.0"},
        method="GET",
    )
    with _no_redirect_opener().open(request, timeout=timeout_seconds) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        return int(response.status), dict(response.headers.items()), body


def _content_type(headers: Mapping[str, str]) -> str | None:
    return next((value for key, value in headers.items() if key.lower() == "content-type"), None)


def _is_json_content_type(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    media_type = value.split(";", 1)[0].strip().lower()
    return media_type == "application/json"


def _fetch_source(
    source_id: str,
    *,
    retrieved_at: str,
    transport: TransportCallable,
) -> TransportObservation:
    descriptor = SOURCE_DESCRIPTORS[source_id]
    url = descriptor["url"]
    try:
        status, headers, body = transport(url, TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        headers = dict(exc.headers.items()) if exc.headers else {}
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    int(exc.code), _content_type(headers), 0, None,
                                    error_code="source_failed:http_status")
    except Exception:
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    None, None, 0, None,
                                    error_code="source_failed:transport_failure")
    content_type = _content_type(headers)
    if not isinstance(body, bytes):
        body_size, digest = 0, None
    else:
        body_size, digest = len(body), hashlib.sha256(body).hexdigest()
    if type(status) is not int or status != 200:
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    status if type(status) is int else None, content_type,
                                    body_size, digest, error_code="source_failed:http_status")
    if not _is_json_content_type(content_type):
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    status, content_type, body_size, digest,
                                    error_code="source_failed:content_type")
    if not isinstance(body, bytes):
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    status, content_type, 0, None,
                                    error_code="source_failed:invalid_transport_body")
    if len(body) > MAX_RESPONSE_BYTES:
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    status, content_type, len(body), digest,
                                    error_code="source_failed:response_too_large")
    try:
        decoded = body.decode("utf-8-sig")
        payload = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    status, content_type, len(body), digest,
                                    error_code="source_failed:invalid_json_or_utf8")
    if not isinstance(payload, list) or any(not isinstance(row, Mapping) for row in payload):
        return TransportObservation(source_id, "source_failed", url, retrieved_at,
                                    status, content_type, len(body), digest,
                                    error_code="source_failed:invalid_json_root_or_row")
    return TransportObservation(source_id, "available" if payload else "unavailable",
                                url, retrieved_at, status, content_type, len(body), digest,
                                tuple(dict(row) for row in payload),
                                None if payload else "unavailable:no_rows")


def _selected_fmtqik(rows: tuple[Mapping[str, Any], ...]) -> Mapping[str, Any]:
    if not rows:
        raise I1ProductionSourceError("unavailable:fmtqik_empty")
    dated: list[tuple[Any, Mapping[str, Any]]] = []
    for row in rows:
        raw = row.get("Date")
        try:
            normalized = parse_twse_roc_date(raw) if isinstance(raw, str) else None
        except (TypeError, ValueError):
            normalized = None
        if normalized is None:
            raise I1ProductionSourceError("source_failed:fmtqik_date_unparseable")
        dated.append((normalized, row))
    latest = max(item[0] for item in dated)
    selected = [row for parsed, row in dated if parsed == latest]
    if len(selected) != 1:
        raise I1ProductionSourceError("source_failed:fmtqik_duplicate_latest_date")
    return selected[0]


def _selected_twse_breadth(rows: tuple[Mapping[str, Any], ...]) -> list[Mapping[str, Any]]:
    selected = [row for row in rows if row.get("類型") == "股票"]
    if len(selected) > 1:
        raise I1ProductionSourceError("source_failed:twse_duplicate_stock_breadth")
    return selected


def _component_from_transport(item: TransportObservation, *, status: str | None = None,
                              official_date: str | None = None) -> dict[str, Any]:
    descriptor = SOURCE_DESCRIPTORS[item.source_id]
    return {
        "status": status or item.status,
        "official_date": official_date,
        "source": {
            "source_id": item.source_id,
            "source_family": descriptor["source_family"],
            "source_contract_id": descriptor["source_contract_id"],
            "url": item.endpoint,
            "authority": "official",
            "retrieved_at": item.retrieved_at,
        },
        "observed_fields": {},
        "unit_metadata": {},
        "transport": {
            "status": item.status,
            "http_status": item.http_status,
            "content_type": item.content_type,
            "response_byte_count": item.response_byte_count,
            "response_sha256": item.response_sha256,
            "error_code": item.error_code,
        },
    }


def _failed_evidence(market: str, retrieved_at: str,
                     components: Mapping[str, dict[str, Any]], status: str,
                     caveat: str) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_CONTRACT,
        "status": status,
        "market": market,
        "currentness_status": "unknown",
        "retrieved_at": retrieved_at,
        "components": dict(components),
        "citation_ids": [],
        "caveats": [caveat],
    }


def _observe_market(
    market: str,
    *,
    retrieved_at: str,
    transport: TransportCallable,
) -> tuple[dict[str, Any], tuple[TransportObservation, ...]]:
    if market == "TWSE":
        fmt = _fetch_source("I1-TWSE-FMTQIK-OPENAPI", retrieved_at=retrieved_at, transport=transport)
        breadth = _fetch_source("I1-TWSE-BREADTH-TWTAZU-OPENAPI", retrieved_at=retrieved_at, transport=transport)
        transports = (fmt, breadth)
        if fmt.status == "source_failed" or breadth.status == "source_failed":
            components = {
                "fmtqik": _component_from_transport(fmt),
                "breadth": _component_from_transport(breadth),
            }
            return _failed_evidence("TWSE", retrieved_at, components, "source_failed",
                                    ";".join(x.error_code or x.status for x in transports if x.status == "source_failed")), transports
        if fmt.status == "unavailable":
            try:
                selected_breadth = _selected_twse_breadth(breadth.rows) if breadth.status == "available" else []
            except I1ProductionSourceError as exc:
                components = {"fmtqik": _component_from_transport(fmt, status="unavailable"),
                              "breadth": _component_from_transport(breadth, status="source_failed")}
                return _failed_evidence("TWSE", retrieved_at, components, "source_failed", str(exc)), transports
            partial = bool(selected_breadth)
            breadth_date = None
            if len(selected_breadth) == 1:
                try:
                    breadth_date = parse_twse_roc_date(selected_breadth[0].get("出表日期")).isoformat()
                except (TypeError, ValueError):
                    breadth_date = None
            components = {"fmtqik": _component_from_transport(fmt, status="unavailable"),
                          "breadth": _component_from_transport(
                              breadth,
                              status="available" if partial else "missing" if breadth.status == "available" else "unavailable",
                              official_date=breadth_date,
                          )}
            return _failed_evidence("TWSE", retrieved_at, components,
                                    "partial" if partial else "unavailable",
                                    "twse_fmtqik_has_no_rows; benchmark_and_turnover_unavailable"), transports
        try:
            fmt_row = _selected_fmtqik(fmt.rows)
            breadth_rows = _selected_twse_breadth(breadth.rows)
            evidence = normalize_twse_market_state([fmt_row], breadth_rows, retrieved_at=retrieved_at)
        except (I1ProductionSourceError, MarketStateNormalizationError) as exc:
            message = str(exc)
            fmt_failed = "fmtqik" in message.lower() or "fmtqik" in message
            breadth_failed = any(marker in message.lower() for marker in ("twse_", "twtaZu".lower(), "breadth", "股票"))
            components = {
                "fmtqik": _component_from_transport(fmt, status="source_failed" if fmt_failed else fmt.status),
                "breadth": _component_from_transport(breadth, status="source_failed" if breadth_failed else breadth.status),
            }
            return _failed_evidence("TWSE", retrieved_at, components, "source_failed", str(exc)), transports
        evidence["components"]["fmtqik"]["transport"] = _transport_json(fmt)
        evidence["components"]["breadth"]["transport"] = _transport_json(breadth)
        return evidence, transports
    if market == "TPEX":
        item = _fetch_source("I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI", retrieved_at=retrieved_at, transport=transport)
        if item.status == "source_failed":
            return _failed_evidence("TPEX", retrieved_at,
                                    {"tpex_mainborad_highlight": _component_from_transport(item)},
                                    "source_failed", item.error_code or "source_failed"), (item,)
        if item.status == "unavailable":
            return _failed_evidence("TPEX", retrieved_at,
                                    {"tpex_mainborad_highlight": _component_from_transport(item, status="unavailable")},
                                    "unavailable", "tpex_highlight_has_no_rows"), (item,)
        if len(item.rows) != 1:
            return _failed_evidence("TPEX", retrieved_at,
                                    {"tpex_mainborad_highlight": _component_from_transport(item)},
                                    "source_failed", "source_failed:tpex_expected_exactly_one_row"), (item,)
        try:
            evidence = normalize_tpex_market_state(item.rows, retrieved_at=retrieved_at)
        except MarketStateNormalizationError as exc:
            return _failed_evidence("TPEX", retrieved_at,
                                    {"tpex_mainborad_highlight": _component_from_transport(item)},
                                    "source_failed", str(exc)), (item,)
        evidence["components"]["tpex_mainborad_highlight"]["transport"] = _transport_json(item)
        return evidence, (item,)
    raise OrchestrationError("market_mismatch")


def _transport_json(item: TransportObservation) -> dict[str, Any]:
    return {
        "status": item.status,
        "http_status": item.http_status,
        "content_type": item.content_type,
        "response_byte_count": item.response_byte_count,
        "response_sha256": item.response_sha256,
        "error_code": item.error_code,
    }


def _targets(requests: tuple[dict[str, Any], ...], market: str) -> list[tuple[dict[str, Any], str]]:
    if not requests or len(requests) > MAX_BATCH_TARGETS:
        raise OrchestrationError("i1_batch_target_count_invalid")
    first = requests[0]
    batch_key = tuple(first.get(name) for name in ("batch_group_id", "executor_id", "capability_id", "market"))
    result: list[tuple[dict[str, Any], str]] = []
    seen: set[str] = set()
    for request in requests:
        if tuple(request.get(name) for name in ("batch_group_id", "executor_id", "capability_id", "market")) != batch_key:
            raise OrchestrationError("batch_dispatch_binding_mismatch")
        if (request.get("schema_version") != "unified_market_evidence_execution_request.v1"
                or request.get("executor_id") != EXECUTOR_ID
                or request.get("capability_id") != CAPABILITY_ID
                or request.get("market") != market
                or request.get("timeout_seconds") != TIMEOUT_SECONDS
                or request.get("maximum_records") != 1):
            raise OrchestrationError("unsupported_production_route")
        identifiers = request.get("approved_security_identifiers")
        security_types = request.get("approved_security_types")
        if not isinstance(identifiers, list) or len(identifiers) != 1 or security_types != ["equity"]:
            raise OrchestrationError("approved_target_binding_invalid")
        canonical = identifiers[0]
        try:
            actual_market, code = canonical.split(":", 1)
        except (AttributeError, ValueError):
            raise OrchestrationError("approved_target_invalid") from None
        if actual_market != market or not code.isascii() or not code.isdigit() or not 1 <= len(code) <= 6:
            raise OrchestrationError("approved_target_market_mismatch")
        if canonical in seen:
            raise OrchestrationError("duplicate_approved_target")
        seen.add(canonical)
        result.append((request, code))
    return result


def _artifact(request: dict[str, Any], context: DispatchRuntimeContext,
              evidence: dict[str, Any]) -> dict[str, Any]:
    path = f"evidence/phase_i/i1/{request['operation_id']}.json"
    evidence["citation_ids"] = [_build_citation_id(request["operation_id"], path)]
    schema = json.loads((ROOT / "schemas" / f"{EVIDENCE_CONTRACT}.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
    if errors:
        raise OrchestrationError("i1_evidence_schema_invalid")
    content = (json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    atomic_write_bytes(context.governed_output_root, path, content)
    return {
        "relative_path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "schema_version": EVIDENCE_CONTRACT,
        "byte_size": len(content),
        "item_count": 1,
    }


def _operation_result(request: dict[str, Any], status: str, artifact: dict[str, Any], caveats: list[str]) -> dict[str, Any]:
    failed = status in {"source_failed", "binding_failed"}
    return {
        "schema_version": RESULT_SCHEMA,
        "operation_id": request["operation_id"],
        "execution_request_id": request["execution_request_id"],
        "execution_request_hash": request["execution_request_hash"],
        "executor_id": EXECUTOR_ID,
        "capability_id": CAPABILITY_ID,
        "evidence_contract": EVIDENCE_CONTRACT,
        "status": "failed" if failed else "succeeded",
        "error_code": status if failed else None,
        "result_item_count": 1,
        "evidence_artifacts": [artifact],
        "warnings": caveats,
    }


def production_batch_operation_adapter_candidate(
    requests: tuple[dict[str, Any], ...],
    context: DispatchRuntimeContext,
    *,
    transport: TransportCallable = _http_transport,
    retrieved_at: str | None = None,
) -> list[dict[str, Any]]:
    """Approved same-market batch candidate; source data is fetched once/group."""
    if context.mode != "execute-approved":
        raise OrchestrationError("production_execution_mode_required")
    _require_approved_execution(requests, context)
    if not requests:
        raise OrchestrationError("batch_dispatch_binding_mismatch")
    market = requests[0].get("market")
    if market not in {"TWSE", "TPEX"}:
        raise OrchestrationError("market_mismatch")
    targets = _targets(requests, market)
    acquired_at = retrieved_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    evidence, _transport = _observe_market(market, retrieved_at=acquired_at, transport=transport)
    output: list[dict[str, Any]] = []
    for request, _code in targets:
        target_evidence = json.loads(json.dumps(evidence, ensure_ascii=False))
        artifact = _artifact(request, context, target_evidence)
        output.append(_operation_result(request, evidence["status"], artifact, list(evidence.get("caveats", []))))
    return output


def production_operation_adapter_candidate(
    request: dict[str, Any], context: DispatchRuntimeContext,
    *, transport: TransportCallable = _http_transport,
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    """Single-operation wrapper over the same governed batching implementation."""
    return production_batch_operation_adapter_candidate(
        (request,), context, transport=transport, retrieved_at=retrieved_at
    )[0]


def build_i1_candidate_runtime_adapter_registry() -> RuntimeAdapterRegistry:
    """Build an isolated test/acceptance candidate registry, never default runtime."""
    raw = json.loads(CANDIDATE_METADATA_PATH.read_text(encoding="utf-8"))["executor_metadata"]
    metadata = ExecutorMetadataRegistry.from_json(raw)
    registrations = []
    for market in ("TWSE", "TPEX"):
        entry = metadata.get_route(EXECUTOR_ID, CAPABILITY_ID, market)
        registrations.append(RuntimeAdapterRegistration(
            executor_id=entry.executor_id,
            capability_id=entry.capability_id,
            market=entry.market,
            supported_security_types=entry.supported_security_types,
            expected_evidence_contract=entry.expected_evidence_contract,
            network_required=entry.network_required,
            bounded_execution_supported=entry.bounded_execution_supported,
            timeout_seconds=entry.timeout_seconds,
            maximum_result_items=entry.maximum_result_items,
            output_policy=entry.output_policy,
            adapter=production_operation_adapter_candidate,
            batch_adapter=production_batch_operation_adapter_candidate,
            fake_adapter=False,
        ))
    return RuntimeAdapterRegistry(registrations)
