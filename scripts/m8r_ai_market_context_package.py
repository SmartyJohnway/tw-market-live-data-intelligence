from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.m8r_bounded_market_context_request import canonical_json
from scripts.m8r_one_shot_market_context_orchestrator import (
    LOCAL_CLASSES,
    RECEIPT_SCHEMA_VERSION,
    RESULT_SCHEMA_VERSION,
)

SCHEMA_VERSION = "ai_market_context.v1"
HASH_SCOPE_SCHEMA_VERSION = "ai_market_context_hash_scope.v1"
ALLOWED_EXECUTION_STATUSES = {"ready", "ready_with_caveats", "partial", "blocked"}
FORBIDDEN_KEYS = {
    "raw_payload", "response_body", "html", "cookies", "cookie", "authorization",
    "api_key", "access_token", "refresh_token", "secret", "password",
    "full_market_rows", "full_market_data",
}
SENSITIVE_DIAGNOSTIC_KEYS = FORBIDDEN_KEYS | {"error", "exception", "detail", "traceback", "message_detail"}
ALLOWED_SOURCES = {
    "TWSE_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_MIS", "TAIFEX_OPENAPI",
    "LOCAL_CONTEXT", "LOCAL_SOURCE_HEALTH", "LOCAL_MARKET_CLOCK",
}
STATUS_ORDER = {"ready": 0, "ready_with_caveats": 1, "partial": 2, "blocked": 3}
BASE_FORBIDDEN = [
    "not_full_market", "not_trading_signal", "not_prediction", "not_recommendation",
    "not_broker_instruction", "not_guaranteed_realtime",
    "not_live_production_ready_without_m8r02a", "not_safe_to_infer_missing_values",
]
PROD = {
    "package_schema_ready": True,
    "offline_packaging_ready": True,
    "production_orchestrator_contract_ready": True,
    "production_executor_adapters_ready": False,
    "production_live_execution_ready": False,
    "m8r_02a_required": True,
    "live_validation_completed": False,
}
CURRENTNESS_MAP = {
    "fresh_intraday_snapshot": "current",
    "active_session_fresh": "current",
    "official_eod_reference": "not_applicable",
    "official_statistics_eod": "not_applicable",
    "regulatory_reference": "not_applicable",
    "reference_metadata": "not_applicable",
    "manual_snapshot": "not_applicable",
    "validation_only": "not_applicable",
    "credential_gated_metadata_only": "not_applicable",
    "source_unavailable": "unknown",
    "source_specific_currentness_unresolved": "unknown",
    "currentness_unresolved": "unknown",
    "not_current": "unknown",
    "unknown": "unknown",
    "stale_intraday_snapshot": "stale",
    "stale_official_statistics_eod": "stale",
    "stale_official_eod": "stale",
}
PROHIBITED_VIEW_PHRASES = {
    "buying opportunity", "will rise", "buy recommendation", "sell recommendation",
    "all data is realtime", "complete market picture", "trading signal", "broker instruction",
}


class AIMarketContextPackageError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _err(code: str) -> None:
    raise AIMarketContextPackageError(code)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _sorted(items: Any) -> list[Any]:
    return sorted(list(items), key=lambda x: canonical_json(x))


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _sorted({canonical_json(item): item for item in items}.values())


def _sha(value: Any, length: int | None = None) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def assert_no_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                _err(f"forbidden_raw_key:{path}.{key}")
            assert_no_forbidden_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_forbidden_keys(item, f"{path}[{index}]")


def _safe_output_scope(scope: Any) -> bool:
    if not isinstance(scope, dict):
        return False
    root = scope.get("artifact_root")
    if not isinstance(root, str) or not root.strip():
        return False
    p = Path(root)
    parts = set(p.parts)
    return not (
        root.startswith("/")
        or ".." in parts
        or root.startswith("frontend/public")
        or root.startswith("research/generated")
        or any(part in {".env", "secrets", "credentials"} for part in parts)
    )


def validate_orchestration_result_for_ai_package(orchestration_result: dict[str, Any]) -> dict[str, Any]:
    assert_no_forbidden_keys(orchestration_result)
    if not isinstance(orchestration_result, dict) or orchestration_result.get("schema_version") != RESULT_SCHEMA_VERSION:
        _err("invalid_orchestration_schema")
    status = orchestration_result.get("execution_status")
    if status not in ALLOWED_EXECUTION_STATUSES:
        _err("invalid_execution_status")
    receipt = orchestration_result.get("execution_receipt")
    if not isinstance(receipt, dict) or receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        _err("invalid_receipt_schema")
    for key in ("receipt_id", "plan_id", "plan_hash", "approval_id"):
        if not receipt.get(key):
            _err(f"missing_{key}")
    if not _safe_output_scope(receipt.get("approved_output_scope")):
        _err("unsafe_output_scope")
    operation_results = orchestration_result.get("operation_results")
    missing_context = orchestration_result.get("missing_context")
    if not isinstance(operation_results, list):
        _err("operation_results_not_list")
    if not isinstance(missing_context, list):
        _err("missing_context_not_list")
    receipt_status = receipt.get("package_status")
    if receipt_status not in ALLOWED_EXECUTION_STATUSES or STATUS_ORDER[receipt_status] < STATUS_ORDER[status]:
        _err("receipt_status_incompatible")
    if receipt.get("approved_operation_count") != len(operation_results):
        _err("approved_operation_count_mismatch")
    if receipt.get("missing_context_count") != len(missing_context):
        _err("missing_context_count_mismatch")
    success_count = sum(
        1
        for result in operation_results
        if result.get("status") == "succeeded"
        and result.get("source_observation")
        and result.get("operation_class") not in LOCAL_CLASSES
    )
    if receipt.get("successful_context_count") != success_count:
        _err("successful_context_count_mismatch")
    return {
        "unsafe_retention": not (
            receipt.get("bounded_retention") is True
            and receipt.get("raw_payload_retained") is False
            and receipt.get("full_market_retained_output") is False
        )
    }


def _approved_targets(orchestration: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    targets = orchestration.get("approved_targets")
    if targets is None:
        plan = orchestration.get("plan") if isinstance(orchestration.get("plan"), dict) else {}
        targets = plan.get("targets")
    if isinstance(targets, list) and targets:
        return deepcopy(targets), "approved_target_projection"
    inferred: dict[str, dict[str, Any]] = {}
    for result in orchestration.get("operation_results", []):
        target_id = result.get("target_id")
        if not target_id or target_id in inferred:
            continue
        observation = result.get("source_observation") or {}
        safe_fields = observation.get("safe_fields") or {}
        parts = str(target_id).split(":")
        target = {
            "target_id": target_id,
            "market": observation.get("market") or (parts[0] if len(parts) > 0 else None),
            "instrument_type": observation.get("instrument_type") or (parts[1] if len(parts) > 1 else None),
            "symbol": observation.get("symbol") or (parts[2] if len(parts) > 2 else None),
            "requested_context_types": [],
            "derivative_identity": deepcopy(safe_fields.get("contract_identity") or result.get("returned_identity") or {}),
        }
        inferred[target_id] = target
    return list(inferred.values()), "inferred_from_operation_result" if inferred else "unavailable"


def _provenance(orchestration: dict[str, Any], target_identity_provenance: str) -> dict[str, Any]:
    receipt = orchestration["execution_receipt"]
    approval = orchestration.get("approval_state") or {}
    return {
        "request_id": orchestration.get("request_id") or approval.get("request_id"),
        "plan_id": receipt.get("plan_id"),
        "plan_hash": receipt.get("plan_hash"),
        "approval_id": receipt.get("approval_id"),
        "receipt_id": receipt.get("receipt_id"),
        "orchestration_result_schema": orchestration.get("schema_version"),
        "execution_started_at_utc": receipt.get("execution_started_at_utc"),
        "execution_finished_at_utc": receipt.get("execution_finished_at_utc"),
        "approval_consumed": bool(receipt.get("approval_consumed")),
        "approved_output_scope": deepcopy(receipt.get("approved_output_scope") or {}),
        "bounded_retention": receipt.get("bounded_retention") is True,
        "raw_payload_retained": receipt.get("raw_payload_retained") is True,
        "full_market_retained_output": receipt.get("full_market_retained_output") is True,
        "m8_context_core_status": (orchestration.get("m8_context_core_status") or {}).get("status"),
        "target_identity_provenance": target_identity_provenance,
        "upstream_package_status": receipt.get("package_status"),
    }


def normalize_context_caveats(observation_caveats: Any, operation_issues: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in _as_list(observation_caveats):
        if isinstance(item, str):
            code = item.strip() or "source_warning"
            normalized.append({"code": code, "severity": "warning", "message": code, "source": "observation_caveat"})
        elif isinstance(item, dict):
            code = str(item.get("code") or "source_warning")
            message = str(item.get("message") or code)
            normalized.append({"code": code, "severity": str(item.get("severity") or "warning"), "message": message, "source": "observation_caveat"})
    for item in _as_list(operation_issues):
        if isinstance(item, str):
            code = item.strip() or "operation_issue"
            message = code
        elif isinstance(item, dict):
            code = str(item.get("code") or "operation_issue")
            message = str(item.get("message") or code)
        else:
            code = "operation_issue"
            message = code
        # Keep stable code/message only. Do not copy exception text or diagnostic fields.
        normalized.append({"code": code, "severity": "warning", "message": message, "source": "operation_issue"})
    return _dedupe_dicts(normalized)


def build_source_context_views(orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    contexts = []
    for result in orchestration.get("operation_results", []):
        if result.get("status") != "succeeded" or result.get("operation_class") in LOCAL_CLASSES:
            continue
        observation = deepcopy(result.get("source_observation") or {})
        if not observation:
            continue
        safe_fields = deepcopy(observation.get("safe_fields") or {})
        ctx = {
            "source_context_id": "amc-src-" + _sha({
                "operation_id": result.get("operation_id"),
                "target_id": result.get("target_id"),
                "source_family": result.get("source_family"),
                "context_type": result.get("context_type"),
            }, 16),
            "target_id": result.get("target_id"),
            "operation_id": result.get("operation_id"),
            "source_id": observation.get("source_id") or result.get("source_family"),
            "source_family": observation.get("source_family") or result.get("source_family"),
            "market": observation.get("market"),
            "symbol": observation.get("symbol"),
            "instrument_type": observation.get("instrument_type"),
            "context_type": observation.get("context_type") or result.get("context_type"),
            "authority_level": observation.get("authority_level"),
            "timing_class": observation.get("timing_class"),
            "source_timestamp": observation.get("source_timestamp") or (safe_fields.get("source_time") or {}).get("source_timestamp"),
            "retrieved_at_utc": observation.get("retrieved_at_utc"),
            "currentness": deepcopy(result.get("currentness") or observation.get("currentness") or safe_fields.get("currentness") or {"status": observation.get("overall_ai_currentness")}),
            "safe_fields": safe_fields,
            "caveats": normalize_context_caveats(observation.get("caveats"), result.get("issues")),
        }
        contexts.append(ctx)
    return _sorted(contexts)


def build_local_views(orchestration: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    health = []
    sessions = []
    for result in orchestration.get("operation_results", []):
        observation = result.get("source_observation") or {}
        safe_fields = observation.get("safe_fields") or {}
        if observation.get("source_id") == "LOCAL_SOURCE_HEALTH":
            health.append({
                "target_id": result.get("target_id"),
                "operation_id": result.get("operation_id"),
                "referenced_source_family": safe_fields.get("referenced_source_family"),
                "artifact_availability": safe_fields.get("artifact_availability"),
                "record_timestamp": observation.get("retrieved_at_utc"),
                "staleness_caveat": safe_fields.get("staleness_caveat"),
                "local_only": True,
            })
        if observation.get("source_id") == "LOCAL_MARKET_CLOCK":
            state = safe_fields.get("market_session_state")
            sessions.append({
                "target_id": result.get("target_id"),
                "operation_id": result.get("operation_id"),
                "target_market": safe_fields.get("target_market") or observation.get("market"),
                "market_session_state": state,
                "calendar_evidence": safe_fields.get("calendar_evidence"),
                "session_caveat": safe_fields.get("calendar_caveat"),
                "resolution_status": "unresolved" if state in (None, "unresolved") else "resolved",
            })
    return _sorted(sessions), _sorted(health)


def _currentness_value(currentness: Any) -> str:
    if isinstance(currentness, dict):
        for key in ("overall_status", "status", "freshness_assessment", "overall_ai_currentness"):
            if currentness.get(key):
                return str(currentness[key])
    if isinstance(currentness, str):
        return currentness
    return "unknown"


def normalize_currentness_status(currentness: Any) -> str:
    return CURRENTNESS_MAP.get(_currentness_value(currentness), "unknown")


def build_currentness_summary(source_contexts: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"unknown_count": 0, "stale_count": 0, "current_count": 0}
    not_applicable_count = 0
    by_source_family: dict[str, list[str]] = {}
    by_target: dict[str, list[str]] = {}
    for context in source_contexts:
        raw = _currentness_value(context.get("currentness"))
        normalized = normalize_currentness_status(context.get("currentness"))
        if normalized == "not_applicable":
            not_applicable_count += 1
        else:
            counts[f"{normalized}_count"] += 1
        by_source_family.setdefault(context.get("source_family"), []).append(raw)
        by_target.setdefault(context.get("target_id"), []).append(raw)
    active = [name for name, count in counts.items() if count]
    if not source_contexts:
        overall = "not_applicable"
    elif len(active) > 1:
        overall = "mixed"
    elif active:
        overall = active[0].replace("_count", "")
    else:
        overall = "not_applicable"
    return {
        "overall_status": overall,
        "by_source_family": {key: sorted(set(value)) for key, value in by_source_family.items()},
        "by_target": {key: sorted(set(value)) for key, value in by_target.items()},
        "not_applicable_count": not_applicable_count,
        **counts,
    }


def build_missing_context_views(orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    return _sorted([
        {
            "target_id": item.get("target_id"),
            "context_type": item.get("context_type"),
            "planned_source_family": item.get("planned_source_family"),
            "reason_code": item.get("reason_code"),
            "operation_status": item.get("operation_status"),
            "usable_fallback": None,
            "forbidden_interpretations": sorted(set(_as_list(item.get("forbidden_interpretations")) + ["not_safe_to_infer_missing_values"])),
        }
        for item in orchestration.get("missing_context", [])
    ])


def build_target_views(approved_targets: list[dict[str, Any]], source_contexts: list[dict[str, Any]], missing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: dict[str, list[str]] = {}
    available: dict[str, set[str]] = {}
    missing_by_target: dict[str, set[str]] = {}
    for context in source_contexts:
        refs.setdefault(context["target_id"], []).append(context["source_context_id"])
        available.setdefault(context["target_id"], set()).add(context["context_type"])
    for item in missing:
        missing_by_target.setdefault(item["target_id"], set()).add(item["context_type"])
    targets = []
    for target in approved_targets:
        target_id = target.get("target_id") or ":".join(str(target.get(key, "")) for key in ("market", "instrument_type", "symbol"))
        requested = target.get("requested_context_types") or sorted(available.get(target_id, set()) | missing_by_target.get(target_id, set()))
        status = "partial" if missing_by_target.get(target_id) else ("ready_with_caveats" if refs.get(target_id) else "blocked")
        targets.append({
            "target_id": target_id,
            "market": target.get("market"),
            "symbol": target.get("symbol"),
            "instrument_type": target.get("instrument_type"),
            "derivative_identity": deepcopy(target.get("derivative_identity") or {}),
            "requested_context_types": sorted(set(requested)),
            "available_context_types": sorted(available.get(target_id, set())),
            "missing_context_types": sorted(missing_by_target.get(target_id, set())),
            "target_status": status,
            "source_context_refs": sorted(set(refs.get(target_id, []))),
            "caveats": [],
            "forbidden_interpretations": [],
        })
    return _sorted(targets)


def build_caveats(package: dict[str, Any], unsafe_reason: str | None = None) -> list[dict[str, Any]]:
    caveats = []

    def add(code: str, severity: str = "warning", scope: str = "package", **extra: Any) -> None:
        caveats.append({"code": code, "severity": severity, "scope": scope, "message": code.replace("_", " "), **{k: v for k, v in extra.items() if v is not None}})

    add("production_executor_adapter_not_ready")
    add("production_live_execution_not_ready")
    if unsafe_reason:
        add(unsafe_reason, "blocking")
    if package.get("missing_context"):
        add("missing_context")
        add("partial_context")
    if package.get("currentness_summary", {}).get("unknown_count"):
        add("currentness_unknown")
    if package.get("currentness_summary", {}).get("stale_count"):
        add("source_stale")
    if package.get("provenance", {}).get("target_identity_provenance") == "inferred_from_operation_result":
        add("approved_target_scope_not_fully_available")
    for session in package.get("market_session_context", []):
        if session.get("resolution_status") == "unresolved":
            add("market_session_unresolved", target_id=session.get("target_id"))
    for health in package.get("source_health_context", []):
        add("source_health_not_live_probe", source_family=health.get("referenced_source_family"))
    for context in package.get("source_contexts", []):
        if context.get("timing_class") == "official_eod":
            add("official_eod_not_intraday", source_family=context.get("source_family"))
        if context.get("timing_class") == "liveish_intraday_snapshot":
            add("liveish_not_exchange_official_realtime", source_family=context.get("source_family"))
        if normalize_currentness_status(context.get("currentness")) == "stale":
            add("source_stale", "warning", "source", target_id=context.get("target_id"), source_family=context.get("source_family"))
    if any(target.get("market") == "TAIFEX" for target in package.get("targets", [])):
        add("taifex_exact_contract_required")
    if package.get("provenance", {}).get("m8_context_core_status") == "build_failed":
        add("m8_context_core_unavailable")
    return _dedupe_dicts(caveats)


def build_forbidden_interpretations(package: dict[str, Any]) -> list[str]:
    codes = set(BASE_FORBIDDEN)
    if package.get("package_status") in {"partial", "blocked"}:
        codes.add("not_complete_when_partial")
    if package.get("currentness_summary", {}).get("overall_status") in {"mixed", "unknown", "stale"}:
        codes.add("not_all_sources_current")
    for context in package.get("source_contexts", []):
        if context.get("timing_class") == "official_eod":
            codes.add("official_eod_not_live")
        if context.get("timing_class") == "liveish_intraday_snapshot":
            codes.add("liveish_not_official_realtime")
    if package.get("source_health_context"):
        codes.add("local_health_not_live_probe")
    if any(session.get("resolution_status") == "unresolved" for session in package.get("market_session_context", [])):
        codes.add("unresolved_session_not_open_or_closed")
    return sorted(codes)


def derive_ai_market_context_status(orchestration: dict[str, Any], package: dict[str, Any], *, unsafe: bool) -> str:
    upstream = orchestration.get("execution_status")
    if unsafe or upstream == "blocked" or (not package.get("source_contexts") and not package.get("source_health_context") and not package.get("market_session_context")):
        return "blocked"
    status = "ready"
    if (
        upstream == "partial"
        or package.get("missing_context")
        or package.get("provenance", {}).get("m8_context_core_status") == "build_failed"
        or package.get("provenance", {}).get("target_identity_provenance") == "inferred_from_operation_result"
    ):
        status = "partial"
    elif package.get("caveats"):
        status = "ready_with_caveats"
    if upstream in STATUS_ORDER and STATUS_ORDER[status] < STATUS_ORDER[upstream]:
        status = upstream
    return status


def build_ai_market_context_hash_scope(package: dict[str, Any]) -> dict[str, Any]:
    return {
        key: package.get(key)
        for key in [
            "schema_version", "package_status", "scope", "provenance", "targets",
            "source_contexts", "market_session_context", "source_health_context",
            "missing_context", "currentness_summary", "caveats",
            "forbidden_interpretations", "production_readiness",
        ]
    }


def compute_ai_market_context_hash(scope: dict[str, Any]) -> str:
    return _sha(scope)


def build_conversation_views(package: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "package_id": package["package_id"],
        "package_status": package["package_status"],
        "targets": [{"target_id": t["target_id"], "status": t["target_status"]} for t in package["targets"]],
        "latest_usable_observations": [
            {
                "target_id": c["target_id"],
                "source_context_id": c["source_context_id"],
                "source_family": c["source_family"],
                "source_timestamp": c["source_timestamp"],
                "retrieved_at_utc": c["retrieved_at_utc"],
                "currentness": c["currentness"],
            }
            for c in package["source_contexts"]
        ],
        "currentness": package["currentness_summary"],
        "highest_severity_caveats": [c for c in package["caveats"] if c["severity"] in {"blocking", "warning"}][:10],
        "missing_context_count": len(package["missing_context"]),
    }
    standard = {
        "package_id": package["package_id"],
        "targets": deepcopy(package["targets"]),
        "source_provenance": deepcopy(package["source_contexts"]),
        "currentness": deepcopy(package["currentness_summary"]),
        "missing_context": deepcopy(package["missing_context"]),
        "caveats": deepcopy(package["caveats"]),
        "forbidden_interpretations": deepcopy(package["forbidden_interpretations"]),
    }
    diagnostic = {
        "package_id": package["package_id"],
        "provenance": deepcopy(package["provenance"]),
        "operation_outcomes": package.get("_operation_outcomes", []),
        "source_mappings": [
            {"target_id": c["target_id"], "operation_id": c["operation_id"], "source_context_id": c["source_context_id"]}
            for c in package["source_contexts"]
        ],
        "identity_evidence": [{"target_id": t["target_id"], "derivative_identity": deepcopy(t.get("derivative_identity"))} for t in package["targets"]],
        "all_caveat_codes": [c["code"] for c in package["caveats"]],
    }
    return {"compact": compact, "standard": standard, "diagnostic": diagnostic}


def build_ai_market_context_package(
    orchestration_result: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
    package_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validate_orchestration_result_for_ai_package(orchestration_result)
    approved_targets, target_identity_provenance = _approved_targets(orchestration_result)
    source_contexts = build_source_context_views(orchestration_result)
    sessions, health = build_local_views(orchestration_result)
    missing = build_missing_context_views(orchestration_result)
    receipt = orchestration_result["execution_receipt"]
    package = {
        "schema_version": SCHEMA_VERSION,
        "package_id": "",
        "generated_at_utc": generated_at_utc or utc_now(),
        "package_status": "blocked",
        "scope": {},
        "provenance": _provenance(orchestration_result, target_identity_provenance),
        "targets": [],
        "source_contexts": source_contexts,
        "market_session_context": sessions,
        "source_health_context": health,
        "missing_context": missing,
        "currentness_summary": build_currentness_summary(source_contexts),
        "caveats": [],
        "forbidden_interpretations": [],
        "conversation_views": {},
        "production_readiness": dict(PROD),
        "integrity": {},
    }
    package["targets"] = build_target_views(approved_targets, source_contexts, missing)
    package["scope"] = {
        "approved_target_count": receipt.get("approved_target_count"),
        "approved_operation_count": receipt.get("approved_operation_count"),
        "successful_context_count": len(source_contexts),
        "missing_context_count": len(missing),
        "markets": sorted({t.get("market") for t in package["targets"] if t.get("market")}),
        "instrument_types": sorted({t.get("instrument_type") for t in package["targets"] if t.get("instrument_type")}),
        "source_families": sorted({c.get("source_family") for c in source_contexts if c.get("source_family")}),
        "requested_context_types": sorted({ctx for t in package["targets"] for ctx in t.get("requested_context_types", [])}),
        "successful_context_types": sorted({c.get("context_type") for c in source_contexts if c.get("context_type")}),
        "missing_context_types": sorted({m.get("context_type") for m in missing if m.get("context_type")}),
        "network_operations_attempted": receipt.get("network_operations_attempted", 0),
        "local_operations_attempted": receipt.get("local_operations_attempted", 0),
        "full_market_scope": False,
        "bounded_target_scope": True,
    }
    package["package_status"] = derive_ai_market_context_status(orchestration_result, package, unsafe=validation["unsafe_retention"])
    package["caveats"] = build_caveats(package, "unsafe_upstream_retention_contract" if validation["unsafe_retention"] else None)
    package["package_status"] = derive_ai_market_context_status(orchestration_result, package, unsafe=validation["unsafe_retention"])
    package["forbidden_interpretations"] = build_forbidden_interpretations(package)
    package["integrity"] = {"package_hash": compute_ai_market_context_hash(build_ai_market_context_hash_scope(package)), "hash_scope_schema": HASH_SCOPE_SCHEMA_VERSION}
    package["package_id"] = "amc-" + package["integrity"]["package_hash"][:16]
    package["_operation_outcomes"] = [
        {"operation_id": r.get("operation_id"), "target_id": r.get("target_id"), "status": r.get("status"), "source_family": r.get("source_family"), "context_type": r.get("context_type")}
        for r in orchestration_result.get("operation_results", [])
    ]
    package["conversation_views"] = build_conversation_views(package)
    package.pop("_operation_outcomes", None)
    validate_ai_market_context_package(package)
    return package


def _validate_view_integrity(package: dict[str, Any]) -> None:
    working = deepcopy(package)
    stored = working.pop("conversation_views", None)
    working["_operation_outcomes"] = (stored or {}).get("diagnostic", {}).get("operation_outcomes", [])
    expected = build_conversation_views(working)
    if stored != expected:
        _err("conversation_view_mismatch")
    text = json.dumps(stored, ensure_ascii=False).lower()
    if any(phrase in text for phrase in PROHIBITED_VIEW_PHRASES):
        _err("conversation_view_mismatch")
    package_id = package.get("package_id")
    if any(view.get("package_id") != package_id for view in stored.values() if isinstance(view, dict)):
        _err("conversation_view_mismatch")


def validate_ai_market_context_package(package: dict[str, Any]) -> dict[str, str]:
    assert_no_forbidden_keys(package)
    if package.get("schema_version") != SCHEMA_VERSION:
        _err("invalid_schema_version")
    expected_hash = compute_ai_market_context_hash(build_ai_market_context_hash_scope(package))
    if package.get("integrity", {}).get("package_hash") != expected_hash or package.get("package_id") != "amc-" + expected_hash[:16]:
        _err("package_hash_mismatch")
    provenance = package.get("provenance") or {}
    if not provenance.get("receipt_id") and package.get("package_status") != "blocked":
        _err("missing_receipt_id")
    if package.get("package_status") != "blocked" and (provenance.get("raw_payload_retained") or provenance.get("full_market_retained_output") or not provenance.get("bounded_retention")):
        _err("unsafe_retention")
    targets = package.get("targets", [])
    target_ids = [target.get("target_id") for target in targets]
    source_ids = [source.get("source_context_id") for source in package.get("source_contexts", [])]
    if len(target_ids) != len(set(target_ids)) or len(source_ids) != len(set(source_ids)):
        _err("duplicate_ids")
    if package.get("scope", {}).get("approved_target_count") != len(targets):
        _err("approved_target_count_mismatch")
    diagnostic_ops = package.get("conversation_views", {}).get("diagnostic", {}).get("operation_outcomes", [])
    if package.get("scope", {}).get("approved_operation_count") != len(diagnostic_ops):
        _err("approved_operation_count_mismatch")
    by_target_available: dict[str, set[str]] = {tid: set() for tid in target_ids}
    by_target_missing: dict[str, set[str]] = {tid: set() for tid in target_ids}
    for source in package.get("source_contexts", []):
        if source.get("target_id") not in target_ids:
            _err("dangling_source_target_ref")
        if source.get("source_family") not in ALLOWED_SOURCES:
            _err("unsafe_source_family")
        by_target_available.setdefault(source.get("target_id"), set()).add(source.get("context_type"))
    for item in package.get("missing_context", []):
        if item.get("target_id") not in target_ids:
            _err("dangling_missing_context_target_ref")
        by_target_missing.setdefault(item.get("target_id"), set()).add(item.get("context_type"))
    for target in targets:
        refs = target.get("source_context_refs", [])
        if len(refs) != len(set(refs)):
            _err("duplicate_target_source_context_refs")
        for ref in refs:
            if ref not in source_ids:
                _err("dangling_source_context_ref")
        tid = target.get("target_id")
        if set(target.get("available_context_types", [])) != by_target_available.get(tid, set()):
            _err("target_available_context_mismatch")
        if set(target.get("missing_context_types", [])) != by_target_missing.get(tid, set()):
            _err("target_missing_context_mismatch")
        if target.get("market") == "TAIFEX":
            identity = target.get("derivative_identity") or {}
            required = ["expiry", "contract_type", "session"] + (["underlying", "strike", "call_put"] if target.get("instrument_type") == "option" else [])
            if any(not identity.get(key) for key in required):
                _err("derivative_identity_incomplete")
    if package.get("scope", {}).get("successful_context_count") != len(package.get("source_contexts", [])):
        _err("wrong_successful_context_count")
    if package.get("scope", {}).get("missing_context_count") != len(package.get("missing_context", [])):
        _err("wrong_missing_context_count")
    if package.get("missing_context") and package.get("package_status") == "ready":
        _err("status_inconsistency")
    upstream = provenance.get("upstream_package_status")
    if upstream in STATUS_ORDER and STATUS_ORDER[package.get("package_status")] < STATUS_ORDER[upstream]:
        _err("status_less_conservative_than_upstream")
    if not set(BASE_FORBIDDEN).issubset(set(package.get("forbidden_interpretations", []))):
        _err("base_forbidden_interpretations_missing")
    if package.get("production_readiness") != PROD:
        _err("unsafe_production_readiness")
    _validate_view_integrity(package)
    return {"status": "valid"}


def write_ai_market_context_artifacts(package: dict[str, Any], *, artifact_root: str | None = None, receipt_id: str | None = None) -> list[str]:
    validate_ai_market_context_package(package)
    approved_root = package.get("provenance", {}).get("approved_output_scope", {}).get("artifact_root")
    approved_receipt = package.get("provenance", {}).get("receipt_id")
    root = approved_root if artifact_root is None else artifact_root
    rid = approved_receipt if receipt_id is None else receipt_id
    if root != approved_root:
        raise OSError("approved_output_scope_mismatch")
    if rid != approved_receipt:
        raise OSError("receipt_identity_mismatch")
    if not _safe_output_scope({"artifact_root": root}):
        raise OSError("unapproved_artifact_root")
    run_dir = Path(root) / rid
    run_dir.mkdir(parents=True, exist_ok=False)
    payloads = {
        "ai_market_context_v1.json": package,
        "ai_market_context_compact.json": package["conversation_views"]["compact"],
        "ai_market_context_standard.json": package["conversation_views"]["standard"],
        "ai_market_context_diagnostic.json": package["conversation_views"]["diagnostic"],
    }
    written = []
    for name, payload in payloads.items():
        assert_no_forbidden_keys(payload)
        fd, tmp = tempfile.mkstemp(prefix=name, dir=run_dir)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, sort_keys=True, indent=2)
        os.replace(tmp, run_dir / name)
        written.append(str(run_dir / name))
    return written
