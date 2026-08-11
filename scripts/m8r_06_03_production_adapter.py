"""Governed M8R-06-03 production adapters for the accepted 05B routes.

This module only materializes trusted registrations.  Network activity occurs
solely when the 05B-03 dispatcher invokes an already approved registration.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.m5k_common import execute_live_observation
from scripts.m8a_tpex_official_eod_adapter import execute_tpex_official_eod_adapter
from scripts.m8a_twse_official_eod_adapter import execute_twse_official_eod_adapter
from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    RuntimeAdapterRegistration,
    RuntimeAdapterRegistry,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_filesystem_safety import atomic_write_bytes


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "config" / "m8r_06_03_executor_registry_metadata.json"
EXECUTOR_ID = "m8r_03d_watchlist_controlled_executor_adapter"
ARTIFACT_SCHEMA_VERSION = "m8r_06_03_operation_evidence.v1"
EVIDENCE_CONTRACTS = {
    "current_observation": "bounded normalized source observation with source health/currentness",
    "official_eod_reference": "official EOD reference plus timing/currentness context",
}


def load_production_executor_metadata() -> dict[str, Any]:
    """Load and structurally validate the fixed committed production authority."""
    payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    ExecutorMetadataRegistry.from_json(payload)
    return payload


def production_executor_metadata_sha256() -> str:
    return hashlib.sha256(METADATA_PATH.read_bytes()).hexdigest()


def _result_base(request: dict[str, Any], *, status: str, error_code: str | None) -> dict[str, Any]:
    return {
        "schema_version": "unified_market_evidence_operation_result.v1",
        "operation_id": request["operation_id"],
        "execution_request_id": request["execution_request_id"],
        "execution_request_hash": request["execution_request_hash"],
        "executor_id": request["executor_id"],
        "capability_id": request["capability_id"],
        "evidence_contract": EVIDENCE_CONTRACTS.get(request["capability_id"], "unknown"),
        "status": status,
        "error_code": error_code,
        "result_item_count": 0,
        "evidence_artifacts": [],
        "warnings": [],
    }


def _require_approved_execution(requests: tuple[dict[str, Any], ...], context: DispatchRuntimeContext) -> None:
    if context.mode != "execute-approved":
        raise OrchestrationError("production_execution_mode_required")
    if any(request.get("network_authorized") is not True for request in requests):
        raise OrchestrationError("network_required_not_authorized")


def _write_safe_evidence(
    request: dict[str, Any],
    context: DispatchRuntimeContext,
    records: list[dict[str, Any]],
    *,
    source_family: str,
) -> dict[str, Any]:
    # ``records`` are already normalized source observations/adapters outputs;
    # neither transport bodies nor headers are persisted here.
    payload = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "operation_id": request["operation_id"],
        "execution_request_id": request["execution_request_id"],
        "source_family": source_family,
        "capability_id": request["capability_id"],
        "market": request["market"],
        "records": records,
    }
    content = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    relative_path = f"evidence/{request['operation_id']}.json"
    atomic_write_bytes(context.governed_output_root, relative_path, content)
    return {
        "relative_path": relative_path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "byte_size": len(content),
        "item_count": len(records),
    }


def _current_observation(request: dict[str, Any], context: DispatchRuntimeContext) -> dict[str, Any]:
    _require_approved_execution((request,), context)
    identifiers = request["approved_security_identifiers"]
    if len(identifiers) != 1:
        return _result_base(request, status="failed", error_code="approved_target_count_invalid")
    canonical_target_id = identifiers[0]
    try:
        market, symbol = canonical_target_id.split(":", 1)
    except ValueError:
        return _result_base(request, status="failed", error_code="approved_target_invalid")
    if market != request["market"]:
        return _result_base(request, status="failed", error_code="approved_target_market_mismatch")
    watchlist = {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": f"m8r06-03-{request['operation_id']}",
        "name": "M8R-06-03 approved target",
        "description": "server constructed from approved 05B execution request",
        "import_export": {"json": True, "csv_future": True},
        "governance": {"trading_signal": False, "recommendations_allowed": False},
        "items": [{
            "id": canonical_target_id,
            "symbol": symbol,
            "display_name": canonical_target_id,
            "market": market.lower(),
            "instrument_type": "equity",
            "adapter": "twse_mis_equity_etf_quote",
            "preferred_sources": ["twse_mis_equity_etf_quote"],
            "category": "m8r_06_03",
            "enabled": True,
            "display_order": 1,
            "tags": ["approved"],
            "notes": "",
        }],
    }
    observation = execute_live_observation(
        watchlist,
        write_latest=False,
        timeout=request["timeout_seconds"],
        allow_individual_fallback=False,
    )
    records = [item for item in observation.get("observations", []) if isinstance(item, dict)]
    if not records:
        return _result_base(request, status="failed", error_code="current_observation_unavailable")
    artifact = _write_safe_evidence(request, context, records, source_family="TWSE_MIS")
    result = _result_base(request, status="succeeded", error_code=None)
    result.update(result_item_count=len(records), evidence_artifacts=[artifact])
    return result


def _official_eod(request: dict[str, Any], context: DispatchRuntimeContext) -> dict[str, Any]:
    _require_approved_execution((request,), context)
    identifiers = request["approved_security_identifiers"]
    if len(identifiers) != 1:
        return _result_base(request, status="failed", error_code="approved_target_count_invalid")
    try:
        market, symbol = identifiers[0].split(":", 1)
    except ValueError:
        return _result_base(request, status="failed", error_code="approved_target_invalid")
    if market != request["market"]:
        return _result_base(request, status="failed", error_code="approved_target_market_mismatch")
    execute = execute_twse_official_eod_adapter if market == "TWSE" else execute_tpex_official_eod_adapter if market == "TPEX" else None
    if execute is None:
        return _result_base(request, status="failed", error_code="unsupported_market")
    source_result = execute([symbol], timeout=request["timeout_seconds"])
    records = [item for item in source_result.get("observations", []) if isinstance(item, dict)]
    if not records:
        return _result_base(request, status="failed", error_code="official_eod_unavailable")
    artifact = _write_safe_evidence(request, context, records, source_family=source_result.get("source_id", "official_eod"))
    result = _result_base(request, status="succeeded", error_code=None)
    result.update(result_item_count=len(records), evidence_artifacts=[artifact])
    return result


def production_operation_adapter(request: dict[str, Any], context: DispatchRuntimeContext) -> dict[str, Any]:
    """Fixed adapter dispatch; no browser-controlled module, path, or URL."""
    if request.get("executor_id") != EXECUTOR_ID:
        raise OrchestrationError("executor_mismatch")
    capability = request.get("capability_id")
    if capability == "current_observation":
        return _current_observation(request, context)
    if capability == "official_eod_reference":
        return _official_eod(request, context)
    raise OrchestrationError("unsupported_capability")


def production_batch_operation_adapter(requests: tuple[dict[str, Any], ...], context: DispatchRuntimeContext) -> list[dict[str, Any]]:
    """One governed source call per canonical compatible batch, then fan out."""
    if not requests:
        raise OrchestrationError("batch_dispatch_binding_mismatch")
    _require_approved_execution(requests, context)
    first = requests[0]
    fields = ("batch_group_id", "executor_id", "capability_id", "market")
    expected_binding = tuple(first.get(field) for field in fields)
    if any(tuple(item.get(field) for field in fields) != expected_binding for item in requests):
        raise OrchestrationError("batch_dispatch_binding_mismatch")
    identifiers = [item["approved_security_identifiers"] for item in requests]
    if any(len(item) != 1 for item in identifiers):
        raise OrchestrationError("approved_target_count_invalid")
    try:
        target_parts = [item[0].split(":", 1) for item in identifiers]
        if any(len(parts) != 2 or parts[0] != first["market"] for parts in target_parts):
            raise ValueError
        symbols = [parts[1] for parts in target_parts]
    except (IndexError, ValueError):
        raise OrchestrationError("approved_target_market_mismatch") from None
    capability, market = first["capability_id"], first["market"]
    if capability == "current_observation":
        watchlist = {
            "schema_version": "m5n_watchlist.v1",
            "watchlist_id": first["batch_group_id"],
            "name": "M8R-06-03 approved batch",
            "description": "server constructed from approved 05B execution requests",
            "import_export": {"json": True, "csv_future": True},
            "governance": {"trading_signal": False, "recommendations_allowed": False},
            "items": [
                {
                    "id": f"{market}:{symbol}",
                    "symbol": symbol,
                    "display_name": f"{market}:{symbol}",
                    "market": market.lower(),
                    "instrument_type": "equity",
                    "adapter": "twse_mis_equity_etf_quote",
                    "preferred_sources": ["twse_mis_equity_etf_quote"],
                    "category": "m8r_06_03",
                    "enabled": True,
                    "display_order": index,
                    "tags": ["approved"],
                    "notes": "",
                }
                for index, symbol in enumerate(symbols, 1)
            ],
        }
        source = execute_live_observation(
            watchlist,
            write_latest=False,
            timeout=first["timeout_seconds"],
            allow_individual_fallback=False,
        )
        records = {str(item.get("symbol")): item for item in source.get("observations", []) if isinstance(item, dict)}
        family = "TWSE_MIS"
    elif capability == "official_eod_reference":
        execute = (
            execute_twse_official_eod_adapter
            if market == "TWSE"
            else execute_tpex_official_eod_adapter
            if market == "TPEX"
            else None
        )
        if execute is None:
            raise OrchestrationError("unsupported_market")
        source = execute(symbols, timeout=first["timeout_seconds"])
        records = {str(item.get("symbol")): item for item in source.get("observations", []) if isinstance(item, dict)}
        family = source.get("source_id", "official_eod")
    else:
        raise OrchestrationError("unsupported_capability")
    results = []
    for request, symbol in zip(requests, symbols, strict=True):
        record = records.get(symbol)
        if record is None:
            results.append(_result_base(request, status="failed", error_code=f"{capability}_unavailable"))
        else:
            artifact = _write_safe_evidence(request, context, [record], source_family=family)
            result = _result_base(request, status="succeeded", error_code=None)
            result.update(result_item_count=1, evidence_artifacts=[artifact])
            results.append(result)
    return results


def build_production_runtime_adapter_registry() -> RuntimeAdapterRegistry:
    """Materialize exactly the four committed, route-aware production routes."""
    metadata = ExecutorMetadataRegistry.from_json(load_production_executor_metadata())
    registrations = [
        RuntimeAdapterRegistration(
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
            adapter=production_operation_adapter,
            batch_adapter=production_batch_operation_adapter,
            fake_adapter=False,
        )
        for entry in (metadata.get_route(EXECUTOR_ID, capability, market) for capability, market in (
            ("current_observation", "TWSE"),
            ("current_observation", "TPEX"),
            ("official_eod_reference", "TWSE"),
            ("official_eod_reference", "TPEX"),
        ))
    ]
    return RuntimeAdapterRegistry(registrations)
