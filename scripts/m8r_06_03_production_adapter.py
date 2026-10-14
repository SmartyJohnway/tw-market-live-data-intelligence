"""Governed M8R-06-03 production adapters for the accepted 05B routes.

This module only materializes trusted registrations.  Network activity occurs
solely when the 05B-03 dispatcher invokes an already approved registration.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.request import Request, urlopen

from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker

from scripts.m5k_common import execute_live_observation
from scripts.m8_source_freshness_evaluator import build_source_freshness_assessment
from scripts.m8r_03d_watchlist_source_integration import evaluate_evidence_currentness
from scripts.m8r_bounded_market_context_request import load_source_registry
from scripts.m8a_tpex_official_eod_adapter import SOURCE_ID as TPEX_EOD_SOURCE_ID, execute_tpex_official_eod_adapter
from scripts.m8a_twse_official_eod_adapter import SOURCE_ID as TWSE_EOD_SOURCE_ID, execute_twse_official_eod_adapter
from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    RuntimeAdapterRegistration,
    RuntimeAdapterRegistry,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.m8r_05c.citation_builder import _build_citation_id
from server.operational_diagnostics import timed_source_call
from scripts.phase_g.mops_material_disclosures import SOURCE_FAMILY as MATERIAL_DISCLOSURE_SOURCE_FAMILY, execute as execute_material_disclosures
from scripts.phase_g.mops_monthly_revenue import SOURCE_FAMILY as MONTHLY_REVENUE_SOURCE_FAMILY, execute as execute_monthly_revenue
from server.services.phase_h_trading_status_adapters import (
    H1NormalizationError,
    failed_source_result,
    normalize_tpex_attention,
)
from server.services.phase_h_h3_twse_governed_end import resolve_twse_governed_end
from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID as H3_SOURCE_CONTRACT_ID,
    SOURCE_FAMILY as H3_SOURCE_FAMILY,
    TWSEStockDayResult,
    fetch_twse_stock_day_month,
)
from server.services.phase_h_h3_twse_stock_day_walker import collect_twse_stock_day_lookback
from server.services.phase_h_recent_performance import H3DerivationError, build_recent_performance_evidence
from server.services.phase_h_h2_twse_exright_executor import (
    EXECUTOR_ID as PHASE_H_H2_EXECUTOR_ID,
    execute_h2_twse_exright_pre,
)


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "config" / "m8r_06_03_executor_registry_metadata.json"
EXECUTOR_ID = "m8r_03d_watchlist_controlled_executor_adapter"
ARTIFACT_SCHEMA_VERSION = "m8r_06_03_operation_evidence.v1"
EVIDENCE_CONTRACTS = {
    "current_observation": "bounded normalized source observation with source health/currentness",
    "official_eod_reference": "official EOD reference plus timing/currentness context",
    "material_disclosures": "phase_g_material_disclosure_operation_evidence.v1",
    "monthly_revenue": "phase_g_monthly_revenue_operation_evidence.v1",
    "trading_status_context": "trading_status_context_evidence.v1",
    "recent_performance": "recent_performance_evidence.v1",
}
RESEARCH_EXECUTOR_ID = "phase_g_official_research_executor"
RESEARCH_CAPABILITIES = frozenset({"material_disclosures", "monthly_revenue"})

PHASE_H_H1_EXECUTOR_ID = "phase_h_h1_tpex_attention_executor"
PHASE_H_H1_COMPOSITE_EXECUTOR_ID = "phase_h_h1_tpex_composite_executor"
PHASE_H_H1_SOURCE_ID = "H1-TPEX-ATTENTION-OPENAPI"
PHASE_H_H1_TPEX_ATTENTION_URL = "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information"
PHASE_H_H3_EXECUTOR_ID = "phase_h_h3_twse_recent_performance_executor"
PHASE_H_H3_SOURCE_ID = "H3-TWSE-DEFAULT-BOUNDED"
PHASE_H_H3_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
PHASE_H_H3_MAX_UNIQUE_MONTH_REQUESTS = 3
PHASE_H_H2_SOURCE_ID = "H2-TWSE-EXRIGHT-PRE-OPENAPI"
_H3_OBSERVATION_FIELDS = {
    "canonical_target_id", "market", "security_code", "trade_date", "close", "volume",
    "source_family", "source_contract_id", "retrieved_at", "citation_ids",
}


def _h3_failed_month(result: TWSEStockDayResult, *, status: str, code: str) -> TWSEStockDayResult:
    return TWSEStockDayResult(
        status=status,
        source_contract_id=result.source_contract_id,
        requested_month=result.requested_month,
        requested_url=result.requested_url,
        effective_url=result.effective_url,
        http_status=result.http_status,
        content_type=result.content_type,
        retrieved_at=result.retrieved_at,
        response_byte_count=result.response_byte_count,
        response_sha256=result.response_sha256,
        error_code=code,
    )


def _validate_h3_month_result(
    result: TWSEStockDayResult,
    *,
    target: dict[str, str],
    requested_month: str,
    retrieved_at: str,
) -> TWSEStockDayResult:
    """Keep source drift, binding errors and empty coverage distinct."""
    if not isinstance(result, TWSEStockDayResult):
        return TWSEStockDayResult(
            status="source_failed", requested_month=requested_month,
            error_code="source_failed:invalid_month_result_type",
        )
    if result.requested_month != requested_month:
        return _h3_failed_month(result, status="source_failed", code="source_failed:requested_month_mismatch")
    if result.status in {"source_failed", "binding_failed"}:
        return result
    if result.status not in {"available", "no_evidence_in_covered_scope"}:
        return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_month_status")
    if result.source_contract_id != H3_SOURCE_CONTRACT_ID:
        return _h3_failed_month(result, status="source_failed", code="source_failed:source_contract_mismatch")
    if result.retrieved_at != retrieved_at:
        return _h3_failed_month(result, status="source_failed", code="source_failed:retrieved_at_mismatch")
    if not isinstance(result.observations, tuple) or not isinstance(result.unusable_observations, tuple):
        return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_normalized_rows")
    if result.unusable_observation_count != len(result.unusable_observations):
        return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_unusable_row_count")
    if (result.status == "available") != bool(result.observations):
        return _h3_failed_month(result, status="source_failed", code="source_failed:inconsistent_month_coverage")
    seen: dict[str, Mapping[str, Any]] = {}
    for row in result.observations:
        if not isinstance(row, Mapping) or set(row) != _H3_OBSERVATION_FIELDS:
            return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_normalized_row")
        if any(row.get(key) != target[key] for key in ("canonical_target_id", "market", "security_code")):
            return _h3_failed_month(result, status="binding_failed", code="binding_failed:target_identity_mismatch")
        trade_date = row.get("trade_date")
        try:
            parsed_date = date.fromisoformat(trade_date) if isinstance(trade_date, str) else None
        except ValueError:
            parsed_date = None
        close = row.get("close")
        volume = row.get("volume")
        citations = row.get("citation_ids")
        try:
            close_is_finite = not isinstance(close, bool) and isinstance(close, (int, float)) and math.isfinite(close)
        except (OverflowError, TypeError):
            close_is_finite = False
        if (
            parsed_date is None or parsed_date.isoformat() != trade_date or trade_date[:7] != requested_month
            or not close_is_finite or close < 0
            or isinstance(volume, bool) or not isinstance(volume, int) or volume < 0
            or row.get("source_family") != H3_SOURCE_FAMILY
            or row.get("source_contract_id") != H3_SOURCE_CONTRACT_ID
            or row.get("retrieved_at") != retrieved_at
            or not isinstance(citations, list) or not citations
            or any(not isinstance(item, str) or not item.strip() for item in citations)
            or len(set(citations)) != len(citations)
        ):
            return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_normalized_row")
        existing = seen.get(trade_date)
        if existing is not None and dict(existing) != dict(row):
            return _h3_failed_month(result, status="source_failed", code="source_failed:conflicting_duplicate_trade_date")
        seen.setdefault(trade_date, row)
    for row in result.unusable_observations:
        if (
            not isinstance(row, Mapping)
            or set(row) != {"trade_date", "reason"}
            or row.get("reason") != "close_unavailable"
            or not isinstance(row.get("trade_date"), str)
        ):
            return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_unusable_row")
        try:
            parsed_date = date.fromisoformat(row["trade_date"])
        except ValueError:
            parsed_date = None
        if parsed_date is None or parsed_date.isoformat() != row["trade_date"] or row["trade_date"][:7] != requested_month:
            return _h3_failed_month(result, status="source_failed", code="source_failed:invalid_unusable_row")
    return result


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
        "transport_mode": os.environ.get("M8R_06_03_TRANSPORT_MODE", "production_transport"),
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


def _write_research_evidence(
    request: dict[str, Any], context: DispatchRuntimeContext, evidence: dict[str, Any]
) -> dict[str, Any]:
    contract = EVIDENCE_CONTRACTS[request["capability_id"]]
    schema_path = ROOT / "schemas" / f"{contract}.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
    if errors:
        raise OrchestrationError("research_evidence_schema_invalid")
    content = (json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    relative_path = f"evidence/{request['operation_id']}.json"
    atomic_write_bytes(context.governed_output_root, relative_path, content)
    item_count = len(evidence.get("items", [])) if request["capability_id"] == "material_disclosures" else 1
    return {
        "relative_path": relative_path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "schema_version": contract,
        "byte_size": len(content),
        "item_count": item_count,
    }


def _fetch_official_payload(url: str, *, timeout: int) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "text/csv, application/json",
            "User-Agent": "tw-market-live-data-intelligence/1.0",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _research_targets(requests: tuple[dict[str, Any], ...]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for request in requests:
        identifiers = request.get("approved_security_identifiers", [])
        if len(identifiers) != 1:
            raise OrchestrationError("approved_target_count_invalid")
        try:
            market, security_code = identifiers[0].split(":", 1)
        except ValueError:
            raise OrchestrationError("approved_target_invalid") from None
        if market != request.get("market"):
            raise OrchestrationError("approved_target_market_mismatch")
        targets.append({
            "canonical_target_id": identifiers[0],
            "market": market,
            "security_code": security_code,
        })
    return targets


def _research_batch_operation_adapter(
    requests: tuple[dict[str, Any], ...], context: DispatchRuntimeContext
) -> list[dict[str, Any]]:
    _require_approved_execution(requests, context)
    first = requests[0]
    if first.get("executor_id") != RESEARCH_EXECUTOR_ID:
        raise OrchestrationError("executor_mismatch")
    binding = tuple(first.get(field) for field in ("batch_group_id", "executor_id", "capability_id", "market"))
    if any(tuple(item.get(field) for field in ("batch_group_id", "executor_id", "capability_id", "market")) != binding for item in requests):
        raise OrchestrationError("batch_dispatch_binding_mismatch")
    capability = first["capability_id"]
    if capability not in RESEARCH_CAPABILITIES:
        raise OrchestrationError("unsupported_capability")
    targets = _research_targets(requests)
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    timeout = first["timeout_seconds"]
    execute = execute_material_disclosures if capability == "material_disclosures" else execute_monthly_revenue
    source_family = MATERIAL_DISCLOSURE_SOURCE_FAMILY if capability == "material_disclosures" else MONTHLY_REVENUE_SOURCE_FAMILY

    def timed_fetch(url: str) -> bytes:
        return timed_source_call(
            source_family,
            lambda: _fetch_official_payload(url, timeout=timeout),
            market=first["market"],
            capability_id=capability,
        )

    evidence_items = execute(
        targets,
        first["market"],
        observed_at=observed_at,
        csv_fetcher=timed_fetch,
        json_fetcher=timed_fetch,
    )
    if len(evidence_items) != len(requests):
        raise OrchestrationError("research_evidence_count_mismatch")
    outcomes: list[dict[str, Any]] = []
    for request, evidence in zip(requests, evidence_items, strict=True):
        artifact = _write_research_evidence(request, context, evidence)
        evidence_status = evidence["status"]
        succeeded = evidence_status in {
            "available", "partial", "no_evidence_in_covered_scope", "not_yet_available"
        }
        outcome = _result_base(
            request,
            status="succeeded" if succeeded else "failed",
            error_code=None if succeeded else evidence_status,
        )
        result_count = len(evidence.get("items", [])) if capability == "material_disclosures" else int(evidence.get("value") is not None)
        outcome.update(
            result_item_count=result_count,
            evidence_artifacts=[artifact],
            warnings=list(evidence.get("caveats", [])),
        )
        outcomes.append(outcome)
    return outcomes


def _assess_current_observation(item: dict[str, Any], source_policy: dict[str, Any], *, now_utc: str | None = None) -> dict[str, Any]:
    """Delegate timing decisions; acquisition time is the replayable reference clock.

    M8 supplies source-family semantics. The accepted 03D evaluator supplies
    source-age semantics when an authoritative intraday source time exists.
    Retrieved-only observations retain M8 semantics when source policy allows.
    An explicit replay clock may be supplied; production defaults to acquisition.
    Neither clock is rewritten and no threshold is duplicated here.
    """
    observation = {
        "source_id": item.get("source"),
        "source_timestamp": item.get("source_timestamp"),
        "retrieved_at_utc": item.get("retrieved_at_utc") or item.get("retrieved_at"),
        "source_unavailable": item.get("source_unavailable", False),
        "source_unavailable_reason": item.get("source_unavailable_reason"),
        "value_status": item.get("value_status"),
        "market_date": item.get("market_date"),
        "trading_date": item.get("trading_date"),
        "session_state": item.get("session_state"),
    }
    reference_clock = now_utc if now_utc is not None else observation["retrieved_at_utc"]
    policy = source_policy.get("freshness_evaluator_policy", {})
    policy_valid = (isinstance(policy, dict)
                    and isinstance(policy.get("max_intraday_age_seconds"), int)
                    and not isinstance(policy.get("max_intraday_age_seconds"), bool)
                    and policy["max_intraday_age_seconds"] >= 0)
    # M8 owns retrieval-age classification. Invalid policy cannot invoke its
    # compatibility default as current production authority.
    assessment_policy = source_policy if (isinstance(policy, dict) and (policy_valid or source_policy.get("timing_class") != "liveish_intraday_snapshot")) else {**source_policy, "freshness_evaluator_policy": {}}
    assessment = build_source_freshness_assessment(
        observation, assessment_policy, now_utc=reference_clock or "invalid"
    )
    if (source_policy.get("source_id") == observation["source_id"]
            and source_policy.get("timing_class") == "liveish_intraday_snapshot"
            and assessment["freshness_assessment"] != "source_unavailable"):
        # Missing policy/timing is unresolved, never an implicit default policy
        # or a retrieval timestamp masquerading as exchange time.
        retrieved_only_allowed = (policy_valid
                                  and policy.get("allow_retrieved_at_only_intraday_freshness") is True
                                  and policy.get("requires_exchange_timestamp_for_fresh") is False)
        if not policy_valid or assessment["freshness_assessment"] == "unknown":
            currentness = {"status": "unresolved", "reason": "insufficient_policy_or_timing_authority"}
        elif not observation["source_timestamp"]:
            if retrieved_only_allowed:
                currentness = {
                    "status": {"fresh_intraday_snapshot": "fresh", "stale_intraday_snapshot": "stale"}[assessment["freshness_assessment"]],
                    "reason": assessment["freshness_reason"],
                    "age_seconds": assessment["age_seconds"],
                }
            else:
                currentness = {"status": "unresolved", "reason": "exchange_timestamp_required_by_source_policy"}
        else:
            currentness = evaluate_evidence_currentness(
                reference_clock_str=reference_clock,
                source_timestamp_str=observation["source_timestamp"],
                retrieved_at_str=observation["retrieved_at_utc"],
                timing_class=source_policy["timing_class"],
                max_age_seconds=policy["max_intraday_age_seconds"],
            )
        assessment.update(
            status=currentness["status"],
            freshness_assessment={"fresh": "fresh_intraday_snapshot", "stale": "stale_intraday_snapshot", "unresolved": "unknown"}[currentness["status"]],
            freshness_reason=currentness["reason"],
            age_seconds=currentness.get("age_seconds"),
            delay_seconds=currentness.get("transport_latency_seconds"),
            safe_for_ai_context=currentness["status"] == "fresh",
        )
        if currentness["status"] != "fresh":
            assessment["requires_caveats"] = True
            assessment["blocked_interpretation"] = sorted(set(assessment["blocked_interpretation"] + ["not current market evidence"]))
            assessment["allowed_interpretation"] = [value for value in assessment["allowed_interpretation"] if value != "bounded live-ish observation"]
        if currentness["status"] == "stale":
            assessment["stale_reason"] = currentness["reason"]
    elif source_policy.get("source_id") != observation["source_id"]:
        assessment.update(status="unresolved", freshness_assessment="unknown", safe_for_ai_context=False)
    canonical = lambda value: hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assessment.update(
        currentness_policy="family_specific",
        evaluation_timestamp=reference_clock,
        evaluator_id="m8_source_freshness_evaluator+m8r_03d_watchlist_source_integration",
        evaluator_input_sha256=canonical(observation),
        source_policy_sha256=canonical(source_policy),
    )
    return assessment


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
    observation = timed_source_call(
        "TWSE_MIS",
        lambda: execute_live_observation(
            watchlist,
            write_latest=False,
            timeout=request["timeout_seconds"],
            allow_individual_fallback=False,
        ),
        market=market,
        capability_id="current_observation",
    )
    records = [item for item in observation.get("observations", []) if isinstance(item, dict)]
    if not records:
        return _result_base(request, status="failed", error_code="current_observation_unavailable")
    registry = load_source_registry(str(ROOT / "docs/data_capabilities/m8_source_capability_registry.json"))
    policy = next((source for source in registry["sources"] if source.get("source_id") == "TWSE_MIS"), {})
    records = [{**item, "governed_currentness": _assess_current_observation(item, policy)} for item in records]
    artifact = _write_safe_evidence(request, context, records, source_family="TWSE_MIS")
    result = _result_base(request, status="succeeded", error_code=None)
    result.update(result_item_count=len(records), evidence_artifacts=[artifact])
    if any(item["governed_currentness"].get("status") == "stale" for item in records):
        # Existing receipt/Audit warning vocabulary carries the same typed
        # assessment without changing transport success or the public schema.
        result["warnings"].append("stale_intraday_snapshot")
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
    source_id = TWSE_EOD_SOURCE_ID if market == "TWSE" else TPEX_EOD_SOURCE_ID
    source_result = timed_source_call(
        source_id,
        lambda: execute([symbol], timeout=request["timeout_seconds"]),
        market=market,
        capability_id="official_eod_reference",
    )
    records = [item for item in source_result.get("observations", []) if isinstance(item, dict)]
    if not records:
        return _result_base(request, status="failed", error_code="official_eod_unavailable")
    artifact = _write_safe_evidence(request, context, records, source_family=source_result.get("source_id", "official_eod"))
    result = _result_base(request, status="succeeded", error_code=None)
    result.update(result_item_count=len(records), evidence_artifacts=[artifact])
    return result



def _phase_h_artifact_record(
    request: dict[str, Any],
    context: DispatchRuntimeContext,
    *,
    relative_path: str,
    payload: dict[str, Any],
    role: str,
) -> dict[str, Any]:
    """Validate and persist one target-bounded Phase H artifact."""
    schema_version = payload.get("schema_version")
    schema_path = ROOT / "schemas" / f"{schema_version}.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestrationError("phase_h_evidence_schema_unavailable") from exc
    validator = Draft202012Validator(schema) if schema.get("$schema", "").endswith("2020-12/schema") else Draft7Validator(schema)
    if list(validator.iter_errors(payload)):
        raise OrchestrationError("phase_h_evidence_schema_invalid")
    content = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    atomic_write_bytes(context.governed_output_root, relative_path, content)
    item_count = len(payload.get("items", [])) if isinstance(payload.get("items"), list) else 1
    return {
        "relative_path": relative_path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "schema_version": schema_version,
        "byte_size": len(content),
        "item_count": item_count,
        "evidence_contract": schema_version,
        "artifact_role": role,
    }


def _phase_h_h1_sidecar(
    evidence: dict[str, Any],
    *,
    evidence_path: str,
    target: dict[str, str],
    outcome: str,
    failure_code: str | None,
) -> dict[str, Any]:
    source = evidence["source"]
    return {
        "schema_version": "phase_h_source_attempt_governance.v1",
        "evidence_artifact_reference": evidence_path,
        "canonical_target_id": target["canonical_target_id"],
        "capability_id": "trading_status_context",
        "attempts": [{
            "source_family": source["source_family"],
            "source_contract_id": source["source_contract_id"],
            "source_role": source["source_role"],
            "activation_state": source["activation_state"],
            "provider_availability": "not_required",
            "license_authority": source["license_authority"],
            "coverage_result": evidence["status"],
            "outcome": outcome,
            "failure_code": failure_code,
            "citation_ids": evidence["citation_ids"],
        }],
    }


def _phase_h_h1_result_base(
    request: dict[str, Any], *, status: str, error_code: str | None
) -> dict[str, Any]:
    return {
        "schema_version": "unified_market_evidence_operation_result.v2",
        "operation_id": request["operation_id"],
        "execution_request_id": request["execution_request_id"],
        "execution_request_hash": request["execution_request_hash"],
        "executor_id": request["executor_id"],
        "capability_id": request["capability_id"],
        "evidence_contract": "trading_status_context_evidence.v1",
        "status": status,
        "error_code": error_code,
        "result_item_count": 0,
        "evidence_artifacts": [],
        "warnings": [],
    }


def _phase_h_h1_tpex_attention(
    request: dict[str, Any], context: DispatchRuntimeContext
) -> dict[str, Any]:
    """Execute the single H-ACT-H1 route: exact-target TPEx attention."""
    _require_approved_execution((request,), context)
    if request.get("executor_id") != PHASE_H_H1_EXECUTOR_ID:
        raise OrchestrationError("executor_mismatch")
    if request.get("capability_id") != "trading_status_context" or request.get("market") != "TPEX":
        raise OrchestrationError("unsupported_production_route")
    identifiers = request.get("approved_security_identifiers", [])
    if len(identifiers) != 1:
        raise OrchestrationError("approved_target_count_invalid")
    try:
        market, security_code = identifiers[0].split(":", 1)
    except ValueError:
        raise OrchestrationError("approved_target_invalid") from None
    if market != "TPEX":
        raise OrchestrationError("approved_target_market_mismatch")

    target = {
        "canonical_target_id": identifiers[0],
        "market": "TPEX",
        "security_code": security_code,
    }
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    evidence_path = f"evidence/phase_h/h1/{request['operation_id']}.json"
    sidecar_path = f"evidence/phase_h/governance/{request['operation_id']}.json"
    citation_id = _build_citation_id(request["operation_id"], evidence_path)
    failure_code: str | None = None

    try:
        payload = timed_source_call(
            PHASE_H_H1_SOURCE_ID,
            lambda: _fetch_official_payload(PHASE_H_H1_TPEX_ATTENTION_URL, timeout=request["timeout_seconds"]),
            market="TPEX",
            capability_id="trading_status_context",
        )
        rows = json.loads(payload.decode("utf-8-sig"))
        evidence = normalize_tpex_attention(
            rows, target, observed_at=observed_at, citation_id=citation_id
        )
        outcome = "succeeded"
    except (OSError, TimeoutError):
        failure_code = "source_transport_failed"
        evidence = failed_source_result(
            PHASE_H_H1_SOURCE_ID,
            target,
            observed_at=observed_at,
            diagnostic=failure_code,
        )
        outcome = "failed"
    except (UnicodeDecodeError, json.JSONDecodeError):
        failure_code = "source_json_invalid"
        evidence = failed_source_result(
            PHASE_H_H1_SOURCE_ID,
            target,
            observed_at=observed_at,
            diagnostic=failure_code,
        )
        outcome = "failed"
    except H1NormalizationError:
        failure_code = "source_contract_failed"
        evidence = failed_source_result(
            PHASE_H_H1_SOURCE_ID,
            target,
            observed_at=observed_at,
            diagnostic=failure_code,
        )
        outcome = "failed"

    primary = _phase_h_artifact_record(
        request, context, relative_path=evidence_path, payload=evidence, role="primary_evidence"
    )
    sidecar = _phase_h_h1_sidecar(
        evidence,
        evidence_path=evidence_path,
        target=target,
        outcome=outcome,
        failure_code=failure_code,
    )
    governance = _phase_h_artifact_record(
        request, context, relative_path=sidecar_path, payload=sidecar, role="supporting_governance"
    )
    result = _phase_h_h1_result_base(
        request,
        status="succeeded" if outcome == "succeeded" else "failed",
        error_code=failure_code,
    )
    result["result_item_count"] = primary["item_count"] if outcome == "succeeded" else 0
    result["evidence_artifacts"] = [primary, governance]
    if evidence.get("status") == "partial":
        result["warnings"].append("phase_h_h1_partial_coverage")
    return result


def _phase_h_h3_result_base(
    request: dict[str, Any], *, status: str, error_code: str | None
) -> dict[str, Any]:
    return {
        "schema_version": "unified_market_evidence_operation_result.v2",
        "operation_id": request["operation_id"],
        "execution_request_id": request["execution_request_id"],
        "execution_request_hash": request["execution_request_hash"],
        "executor_id": request["executor_id"],
        "capability_id": request["capability_id"],
        "evidence_contract": "recent_performance_evidence.v1",
        "status": status,
        "error_code": error_code,
        "result_item_count": 0,
        "evidence_artifacts": [],
        "warnings": [],
    }


def _phase_h_h3_twse_recent_performance(
    request: dict[str, Any], context: DispatchRuntimeContext
) -> dict[str, Any]:
    """Execute the exact, single-target selected H3 TWSE route once."""
    _require_approved_execution((request,), context)
    if (
        request.get("executor_id") != PHASE_H_H3_EXECUTOR_ID
        or request.get("capability_id") != "recent_performance"
        or request.get("market") != "TWSE"
        or request.get("schema_version") != "unified_market_evidence_execution_request.v2"
    ):
        raise OrchestrationError("unsupported_production_route")
    parameters = request.get("parameters")
    if (
        not isinstance(parameters, dict)
        or set(parameters) != {"lookback_trading_days"}
        or type(parameters.get("lookback_trading_days")) is not int
        or not 1 <= parameters["lookback_trading_days"] <= 20
    ):
        raise OrchestrationError("execution_request_parameters_invalid")
    identifiers = request.get("approved_security_identifiers")
    security_types = request.get("approved_security_types")
    if not isinstance(identifiers, list) or len(identifiers) != 1:
        raise OrchestrationError("approved_target_count_invalid")
    if not isinstance(security_types, list) or security_types != ["equity"]:
        raise OrchestrationError("unsupported_security_type")
    try:
        market, security_code = identifiers[0].split(":", 1)
    except (AttributeError, ValueError):
        raise OrchestrationError("approved_target_invalid") from None
    if market != "TWSE" or not (security_code.isascii() and security_code.isdigit() and 1 <= len(security_code) <= 6):
        raise OrchestrationError("approved_target_market_mismatch")

    target = {
        "canonical_target_id": f"TWSE:{security_code}",
        "market": "TWSE",
        "security_code": security_code,
    }
    lookback = parameters["lookback_trading_days"]
    # This is the sole production clock read for end-selection and H3 evidence.
    execution_timestamp = datetime.now(timezone.utc)
    month_results: dict[str, TWSEStockDayResult] = {}
    actual_month_order: list[str] = []
    walked = None

    def bounded_month_fetch(**kwargs: Any) -> TWSEStockDayResult:
        month = kwargs.get("requested_month")
        if not isinstance(month, str):
            return TWSEStockDayResult(status="source_failed", error_code="source_failed:invalid_requested_month")
        cached = month_results.get(month)
        if cached is not None:
            return cached
        if len(month_results) >= PHASE_H_H3_MAX_UNIQUE_MONTH_REQUESTS:
            return TWSEStockDayResult(
                status="source_failed", requested_month=month,
                retrieved_at=kwargs.get("retrieved_at"),
                error_code="source_failed:unique_month_request_budget_exhausted",
            )
        # Caller-supplied timeout is retained; TLS policy and response cap are
        # fixed by the selected route. No retry or redirect behavior is added.
        result = timed_source_call(
            PHASE_H_H3_SOURCE_ID,
            lambda: fetch_twse_stock_day_month(
                target=target,
                instrument_family="company_share",
                instrument_type="common_share",
                requested_month=month,
                retrieved_at=kwargs["retrieved_at"],
                timeout_seconds=request["timeout_seconds"],
                max_response_bytes=PHASE_H_H3_MAX_RESPONSE_BYTES,
                ssl_policy="compatibility",
            ),
            market="TWSE",
            capability_id="recent_performance",
        )
        result = _validate_h3_month_result(
            result,
            target=target,
            requested_month=month,
            retrieved_at=kwargs["retrieved_at"],
        )
        month_results[month] = result
        actual_month_order.append(month)
        return result

    resolution = resolve_twse_governed_end(
        target=target,
        instrument_family="company_share",
        instrument_type="common_share",
        execution_timestamp=execution_timestamp,
        timeout_seconds=request["timeout_seconds"],
        fetch_month=bounded_month_fetch,
    )
    governed_outcome: str | None = None
    caveats: list[str] = []
    observations: tuple[dict[str, Any], ...] = ()
    end_observation = resolution.governed_end_observation
    if resolution.status in {"source_failed", "binding_failed"}:
        governed_outcome = resolution.status
        caveats = [resolution.error_code or resolution.stop_reason]
        end_observation = None
    elif resolution.status == "unavailable":
        end_observation = None
        caveats = [resolution.stop_reason]
    elif resolution.status == "available" and end_observation is not None:
        month_cache = {item.requested_month: item for item in resolution.month_results}

        def walker_month_fetch(**kwargs: Any) -> TWSEStockDayResult:
            month = kwargs.get("requested_month")
            if isinstance(month, str) and month in month_cache:
                return month_cache[month]
            result = bounded_month_fetch(**kwargs)
            if isinstance(month, str) and month in month_results:
                month_cache[month] = result
            return result

        walked = collect_twse_stock_day_lookback(
            target=target,
            instrument_family="company_share",
            instrument_type="common_share",
            governed_end_observation=end_observation,
            lookback_trading_days=lookback,
            retrieved_at=resolution.retrieved_at,
            timeout_seconds=request["timeout_seconds"],
            max_response_bytes=PHASE_H_H3_MAX_RESPONSE_BYTES,
            month_request_budget=resolution.walker_month_request_budget,
            fetch_month=walker_month_fetch,
        )
        observations = walked.observations
        if walked.status in {"source_failed", "binding_failed"}:
            governed_outcome = walked.status
            caveats = [walked.error_code or walked.stop_reason]
        elif walked.status not in {"available", "insufficient", "unavailable"}:
            governed_outcome = "source_failed"
            caveats = [walked.error_code or "invalid_walker_status"]
        else:
            caveats = [] if walked.status == "available" else [walked.stop_reason]
    else:
        governed_outcome = "source_failed"
        end_observation = None
        caveats = [resolution.error_code or "invalid_governed_end_resolution"]

    if os.environ.get("H3_LIVE_ACCEPTANCE_TELEMETRY") == "YES":
        # Explicit live-acceptance-only, bounded transport summary.  This is
        # metadata only (never source HTML) and stays inside the server-owned
        # execution package so the route-level acceptance runner can bind the
        # actual HTTP outcomes without replacing the production adapter.
        telemetry = {
            "schema_version": "phase_h_h3_live_transport_observation.v1",
            "canonical_target_id": target["canonical_target_id"],
            "source_family": H3_SOURCE_FAMILY,
            "source_contract_id": H3_SOURCE_CONTRACT_ID,
            "execution_timestamp": execution_timestamp.isoformat().replace("+00:00", "Z"),
            "lookback_trading_days": lookback,
            "governed_end_resolution_status": resolution.status,
            "governed_end_observation": resolution.governed_end_observation,
            "requested_months": list(actual_month_order),
            "network_request_count": len(actual_month_order),
            "retry_count": 0,
            "month_attempts": [
                {
                    "month": month,
                    "status": item.status,
                    "http_status": item.http_status,
                    "requested_url": item.requested_url,
                    "effective_url": item.effective_url,
                    "content_type": item.content_type,
                    "ssl_policy": "compatibility",
                    "certificate_verification": True,
                    "hostname_verification": True,
                    "response_byte_count": item.response_byte_count,
                    "response_sha256": item.response_sha256,
                    "numeric_close_observation_count": len(item.observations),
                    "close_unavailable_count": item.unusable_observation_count,
                }
                for month in actual_month_order
                for item in [month_results[month]]
            ],
            "walker": None if walked is None else {
                "status": walked.status,
                "requested_lookback": walked.requested_lookback,
                "valid_lookback_count": walked.valid_lookback_count,
                "missing_lookback_count": walked.missing_lookback_count,
                "post_end_rows_excluded": walked.post_end_rows_excluded,
                "stop_reason": walked.stop_reason,
                "selected_trade_dates": [row["trade_date"] for row in walked.observations],
                "unusable_observations": list(walked.unusable_observations),
            },
        }
        telemetry_path = Path(context.governed_output_root).resolve() / "h3-live-transport-summary.json"
        output_root = Path(context.governed_output_root).resolve()
        if telemetry_path.parent != output_root:
            raise OrchestrationError("h3_live_telemetry_path_invalid")
        atomic_write_bytes(
            str(output_root),
            telemetry_path.name,
            (json.dumps(telemetry, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        )

    schema = json.loads((ROOT / "schemas" / "recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
    try:
        evidence = build_recent_performance_evidence(
            target=target,
            observations=observations,
            governed_end_observation=end_observation,
            requested_observations=lookback,
            baseline_lookbacks=[lookback],
            current_volume_basis="completed_session",
            schema=schema,
            historical_average_evidence=None,
            governed_outcome=governed_outcome,
            caveats=caveats,
        )
    except H3DerivationError as exc:
        evidence = build_recent_performance_evidence(
            target=target,
            observations=(),
            governed_end_observation=None,
            requested_observations=lookback,
            baseline_lookbacks=[lookback],
            current_volume_basis="completed_session",
            schema=schema,
            historical_average_evidence=None,
            governed_outcome="source_failed",
            caveats=[str(exc) or "h3_derivation_failed"],
        )

    evidence_path = f"evidence/phase_h/h3/{request['operation_id']}.json"
    sidecar_path = f"evidence/phase_h/governance/{request['operation_id']}.json"
    # Result V3 citations identify governed operation artifacts. The official
    # STOCK_DAY month citations remain on the normalized observations and end.
    evidence["citation_ids"] = [_build_citation_id(request["operation_id"], evidence_path)]
    primary = _phase_h_artifact_record(
        request, context, relative_path=evidence_path, payload=evidence, role="primary_evidence"
    )
    coverage = evidence["coverage_status"]
    failed = coverage in {"source_failed", "binding_failed"}
    citations = evidence["citation_ids"]
    sidecar = {
        "schema_version": "phase_h_source_attempt_governance.v1",
        "evidence_artifact_reference": evidence_path,
        "canonical_target_id": target["canonical_target_id"],
        "capability_id": "recent_performance",
        "attempts": [{
            "source_family": H3_SOURCE_FAMILY,
            "source_contract_id": H3_SOURCE_CONTRACT_ID,
            "source_role": "default_candidate",
            "activation_state": "active",
            "provider_availability": "unknown",
            "license_authority": None,
            "coverage_result": coverage,
            "outcome": "failed" if failed else "succeeded",
            "failure_code": coverage if failed else None,
            "citation_ids": citations,
        }],
    }
    governance = _phase_h_artifact_record(
        request, context, relative_path=sidecar_path, payload=sidecar, role="supporting_governance"
    )
    outcome = _phase_h_h3_result_base(
        request,
        status="failed" if failed else "succeeded",
        error_code=coverage if failed else None,
    )
    # Operation Result V2 and the existing aggregator count the primary typed
    # evidence artifact even when it truthfully records a source failure.
    outcome["result_item_count"] = primary["item_count"]
    outcome["evidence_artifacts"] = [primary, governance]
    outcome["warnings"] = list(evidence["caveats"])
    return outcome

def production_operation_adapter(request: dict[str, Any], context: DispatchRuntimeContext) -> dict[str, Any]:
    """Fixed adapter dispatch; no browser-controlled module, path, or URL."""
    if request.get("executor_id") == RESEARCH_EXECUTOR_ID:
        return _research_batch_operation_adapter((request,), context)[0]
    if request.get("executor_id") == PHASE_H_H1_EXECUTOR_ID:
        return _phase_h_h1_tpex_attention(request, context)
    if request.get("executor_id") == PHASE_H_H1_COMPOSITE_EXECUTOR_ID:
        from server.services.phase_h_h1_tpex_composite import production_composite_adapter
        try:
            return production_composite_adapter(request, context)
        except ValueError as exc:
            raise OrchestrationError(str(exc) or "phase_h_composite_execution_failed") from exc
    if request.get("executor_id") == PHASE_H_H3_EXECUTOR_ID:
        return _phase_h_h3_twse_recent_performance(request, context)
    if request.get("executor_id") == PHASE_H_H2_EXECUTOR_ID:
        return execute_h2_twse_exright_pre(request, context)
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
    if first.get("executor_id") == RESEARCH_EXECUTOR_ID:
        return _research_batch_operation_adapter(requests, context)
    if first.get("executor_id") != EXECUTOR_ID:
        raise OrchestrationError("executor_mismatch")
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
    if (capability, market) not in {
        ("current_observation", "TWSE"),
        ("current_observation", "TPEX"),
        ("official_eod_reference", "TWSE"),
        ("official_eod_reference", "TPEX"),
    }:
        raise OrchestrationError("unsupported_production_route")
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
        source = timed_source_call(
            "TWSE_MIS",
            lambda: execute_live_observation(
                watchlist,
                write_latest=False,
                timeout=first["timeout_seconds"],
                allow_individual_fallback=False,
            ),
            market=market,
            capability_id="current_observation",
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
        source_id = TWSE_EOD_SOURCE_ID if market == "TWSE" else TPEX_EOD_SOURCE_ID
        source = timed_source_call(
            source_id,
            lambda: execute(symbols, timeout=first["timeout_seconds"]),
            market=market,
            capability_id="official_eod_reference",
        )
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


def _phase_i_i1_timed_transport(url: str, timeout_seconds: int):
    from server.services.phase_i_i1_production_candidate import SOURCE_DESCRIPTORS, _http_transport

    match = next((item for item in SOURCE_DESCRIPTORS.items() if item[1]["url"] == url), None)
    if match is None:
        return _http_transport(url, timeout_seconds)
    source_id, descriptor = match
    return timed_source_call(
        source_id,
        lambda: _http_transport(url, timeout_seconds),
        market=descriptor["market"],
        capability_id="market_state_context",
    )


def phase_i_i1_timed_operation_adapter(request: dict[str, Any], context: DispatchRuntimeContext) -> dict[str, Any]:
    from server.services.phase_i_i1_production_candidate import production_operation_adapter_candidate

    return production_operation_adapter_candidate(request, context, transport=_phase_i_i1_timed_transport)


def phase_i_i1_timed_batch_adapter(
    requests: tuple[dict[str, Any], ...], context: DispatchRuntimeContext
) -> list[dict[str, Any]]:
    from server.services.phase_i_i1_production_candidate import production_batch_operation_adapter_candidate

    return production_batch_operation_adapter_candidate(requests, context, transport=_phase_i_i1_timed_transport)


def build_production_runtime_adapter_registry(*, i3_acquire: Any | None = None) -> RuntimeAdapterRegistry:
    """Materialize governed production routes without acquiring sources at build time."""
    # Import after this module is fully initialized: the already-live-tested I1
    # candidate imports the shared approval guard from this module.
    from server.services.phase_i_i1_production_candidate import (
        EXECUTOR_ID as PHASE_I_I1_EXECUTOR_ID,
        production_batch_operation_adapter_candidate,
        production_operation_adapter_candidate,
    )
    from server.services.phase_i_i2_production_candidate import (
        EXECUTOR_ID as PHASE_I_I2_EXECUTOR_ID,
        production_batch_operation_adapter_candidate as i2_batch_adapter,
        production_operation_adapter_candidate as i2_operation_adapter,
    )
    from server.services.phase_i_i3_cash_institutional_flow_production_candidate import (
        build_i3_production_candidate_registrations,
    )

    metadata = ExecutorMetadataRegistry.from_json(load_production_executor_metadata())
    routes = (
        (EXECUTOR_ID, "current_observation", "TWSE"),
        (EXECUTOR_ID, "current_observation", "TPEX"),
        (EXECUTOR_ID, "official_eod_reference", "TWSE"),
        (EXECUTOR_ID, "official_eod_reference", "TPEX"),
        (RESEARCH_EXECUTOR_ID, "material_disclosures", "TWSE"),
        (RESEARCH_EXECUTOR_ID, "material_disclosures", "TPEX"),
        (RESEARCH_EXECUTOR_ID, "monthly_revenue", "TWSE"),
        (RESEARCH_EXECUTOR_ID, "monthly_revenue", "TPEX"),
        (PHASE_H_H1_EXECUTOR_ID, "trading_status_context", "TPEX"),
        (PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "trading_status_context", "TPEX"),
        (PHASE_H_H3_EXECUTOR_ID, "recent_performance", "TWSE"),
        (PHASE_H_H2_EXECUTOR_ID, "corporate_action_context", "TWSE"),
        (PHASE_I_I1_EXECUTOR_ID, "market_state_context", "TWSE"),
        (PHASE_I_I1_EXECUTOR_ID, "market_state_context", "TPEX"),
        (PHASE_I_I2_EXECUTOR_ID, "index_futures_context", "TWSE"),
    )
    registrations = []
    for executor, capability, market in routes:
        # Historical dormant authority replay has no I2 metadata registration.
        # The current A4 validator separately requires its exact single route.
        if executor == PHASE_I_I2_EXECUTOR_ID and not any(
            item.get("executor_id") == executor for item in load_production_executor_metadata()["executors"]
        ):
            continue
        entry = metadata.get_route(executor, capability, market)
        is_i1 = executor == PHASE_I_I1_EXECUTOR_ID
        is_i2 = executor == PHASE_I_I2_EXECUTOR_ID
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
            adapter=i2_operation_adapter if is_i2 else phase_i_i1_timed_operation_adapter if is_i1 else production_operation_adapter,
            batch_adapter=(
                i2_batch_adapter if is_i2 else
                phase_i_i1_timed_batch_adapter
                if is_i1
                else None
                if entry.executor_id in {PHASE_H_H1_EXECUTOR_ID, PHASE_H_H1_COMPOSITE_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID, PHASE_H_H2_EXECUTOR_ID}
                else production_batch_operation_adapter
            ),
            fake_adapter=False,
        ))
    registrations.extend(build_i3_production_candidate_registrations(
        **({} if i3_acquire is None else {"acquire": i3_acquire})
    ))
    return RuntimeAdapterRegistry(registrations)
