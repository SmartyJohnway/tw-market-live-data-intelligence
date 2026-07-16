from __future__ import annotations

import argparse, json, os, sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from typing import Any

from scripts.m8r_derivatives_conversational_intent import parse_derivatives_intent
from scripts.m8r_taifex_current_contract_resolver import CompositeReferenceUniverseProvider, TaifexMisCurrentUniverseProvider, TaifexOpenApiUniverseProvider, resolve_current_contracts, utc_now
from scripts.m8r_bounded_market_context_request import REQUEST_SCHEMA_VERSION, build_approval_artifact, compile_market_context_execution_plan
from scripts.m8r_one_shot_market_context_orchestrator import FilesystemApprovalConsumptionStore, execute_approved_market_context_plan, write_execution_artifacts
from scripts.m8r_ai_market_context_package import AIMarketContextPackageError, build_ai_market_context_package, validate_ai_market_context_package, write_ai_market_context_artifacts


def safe_root(root: str) -> str:
    p = PurePosixPath(root)
    if p.is_absolute() or ".." in p.parts or str(p).startswith(("frontend/public", "research/generated")):
        raise SystemExit("artifact-root must be a bounded relative path")
    return str(p)


def _target(t: dict[str, Any], sources: list[str]) -> dict[str, Any]:
    if t["instrument_type"] == "future":
        return {"market":"TAIFEX", "instrument_type":"future", "symbol":t["product"], "expiry":t["expiry"], "contract_type":t["contract_type"], "session":t["session"], "requested_source_families":sources, "resolution_mode":"conversational_current"}
    return {"market":"TAIFEX", "instrument_type":"option", "symbol":t["product"], "underlying":t["underlying"], "expiry":t["expiry"], "strike":t["strike"], "call_put":t["call_put"], "contract_type":t["contract_type"], "session":t["session"], "requested_source_families":sources, "resolution_mode":"conversational_current"}


def conversation_resolution_projection(record: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version":"m8r_ai_conversation_resolution.v1", "original_intent_summary": record.get("original_user_text"), "resolved_contracts": record.get("resolved_exact_targets", []), "assumptions": record.get("assumptions", []), "reference_basis": record.get("reference_observation", {}), "contract_resolution_time_utc": record.get("discovered_universe_summary", {}).get("discovered_at_utc") or utc_now(), "reresolution_performed": bool(record.get("reresolution_count")), "reresolution_count": record.get("reresolution_count", 0), "raw_payload_retained": False}


def openapi_tx_reference() -> str | None:
    provider = TaifexOpenApiUniverseProvider()
    universe = provider.discover({"instrument_family": "future", "product": "TX"})
    ref = provider.reference({"instrument_family": "future", "product": "TX"}, universe)
    return ref.get("reference_value")




def _primary_provider(resolver: Any) -> Any:
    return getattr(resolver, "primary", resolver)


def _provider_diagnostics(resolver: Any) -> list[dict[str, Any]]:
    return list(getattr(_primary_provider(resolver), "diagnostics", []) or [])


def _classify_failure_layer(resolution: dict[str, Any], operation_results: list[dict[str, Any]] | None = None, ai_state: dict[str, Any] | None = None, provider_diagnostics: list[dict[str, Any]] | None = None) -> str | None:
    status = resolution.get("resolution_status")
    provider_diagnostics = provider_diagnostics or []
    if status == "reference_unavailable":
        return "current_reference_unavailable"
    for d in provider_diagnostics:
        c = d.get("counts", {})
        if c.get("selected_chain_request_status") == "failed":
            return "selected_option_chain_fetch_failed"
    if status == "no_current_contract_resolved":
        assumptions = {a.get("code") for a in resolution.get("assumptions", [])}
        if "reference_unavailable" in assumptions:
            return "current_reference_unavailable"
        return "no_near_reference_strike"
    fresh = resolution.get("freshness_check") or {}
    if status == "freshness_check_failed" or fresh.get("valid") is False and fresh.get("reason"):
        return "freshness_identity_disappeared"
    op_results = operation_results or []
    for op in op_results:
        if op.get("source_family") != "TAIFEX_MIS" or op.get("status") in {"succeeded", "success"}:
            continue
        issue_text = json.dumps(op.get("issues") or op.get("warnings") or op, ensure_ascii=False)
        if any(token in issue_text for token in ["source_identity", "requested_month_not_available", "requested_strike_not_available", "option_exact_identity_not_unique", "runtime_symbol_mismatch"]):
            return "production_exact_identity_resolution_failed"
        return "production_detail_fetch_failed"
    if ai_state and ai_state.get("status") == "build_failed":
        return "ai_package_build_failed"
    return None


def write_mis_diagnostic(root: str, resolver: Any, resolution: dict[str, Any], *, operation_results: list[dict[str, Any]] | None = None, ai_state: dict[str, Any] | None = None) -> dict[str, Any]:
    provider_diags = _provider_diagnostics(resolver)
    discover = [d for d in provider_diags if d.get("stage") == "discover"]
    references = [d for d in provider_diags if d.get("stage") == "reference"]
    first = discover[0] if discover else {}
    final = discover[-1] if discover else {}
    counts = first.get("counts", {})
    final_counts = final.get("counts", {})
    operation_results = operation_results or []
    mis_ops = [op for op in operation_results if op.get("source_family") == "TAIFEX_MIS"]
    runtime_ids = []
    for op in mis_ops:
        ident = op.get("returned_identity") or {}
        safe = (((op.get("source_observation") or {}).get("safe_fields") or {}).get("contract_identity") or {})
        rid = ident.get("runtime_symbol_id") or safe.get("runtime_symbol_id") or ident.get("runtime_symbol") or safe.get("runtime_symbol")
        if rid:
            runtime_ids.append(str(rid))
    selector_status = "not_run" if not operation_results else ("succeeded" if any(op.get("status") in {"succeeded", "success"} for op in mis_ops) else "failed")
    ai_state = ai_state or {"status": "not_run"}
    diagnostic = {
        "schema_version": "m8r_mis_conversational_resolution_diagnostic.v1",
        "generated_at_utc": utc_now(),
        "products_request_status": "succeeded" if counts.get("products", 0) else "unknown_or_failed",
        "months_request_status": "succeeded" if counts.get("months", 0) else "unknown_or_failed",
        "available_expiries": first.get("available_expiries") or resolution.get("discovered_universe_summary", {}).get("available_expiries", []),
        "selected_expiry": counts.get("selected_expiry") or resolution.get("discovered_universe_summary", {}).get("selected_expiry"),
        "selected_contract_type": counts.get("selected_contract_type") or resolution.get("discovered_universe_summary", {}).get("selected_contract_type"),
        "selected_chain_request_status": counts.get("selected_chain_request_status"),
        "selected_chain_row_count": counts.get("option_rows_examined", 0),
        "normalized_identity_count": counts.get("contracts", 0),
        "strike_range": {"min": counts.get("strike_min"), "max": counts.get("strike_max"), "count": counts.get("strike_count", 0)},
        "call_count": counts.get("call_count", 0),
        "put_count": counts.get("put_count", 0),
        "option_chain_fetch_count": sum((d.get("counts", {}) or {}).get("option_chain_fetch_count", 0) for d in discover),
        "option_rows_examined_total": sum((d.get("counts", {}) or {}).get("option_rows_examined", 0) for d in discover),
        "freshness_second_discovery_result": {
            "performed": bool(resolution.get("second_discovery_performed")),
            "valid": (resolution.get("freshness_check") or {}).get("valid"),
            "reason": (resolution.get("freshness_check") or {}).get("reason"),
            "available_expiries": final.get("available_expiries") or resolution.get("discovered_universe_summary", {}).get("freshness_available_expiries", []),
            "selected_chain_row_count": final_counts.get("option_rows_examined", 0),
            "normalized_identity_count": final_counts.get("contracts", 0),
        },
        "reference_acquisition_result": (references[-1].get("reference_acquisition_result") if references else resolution.get("reference_observation", {})),
        "resolved_exact_targets": resolution.get("resolved_exact_targets", []),
        "production_selector_status": selector_status,
        "runtime_symbol_ids": sorted(set(runtime_ids)),
        "operation_result_status": [{"source_family": op.get("source_family"), "status": op.get("status"), "reason": op.get("reason_code") or op.get("reason")} for op in operation_results],
        "ai_package_status": {"status": ai_state.get("status"), "package_id": ai_state.get("package_id"), "reason": ai_state.get("reason")},
        "failure_layer": _classify_failure_layer(resolution, operation_results, ai_state, provider_diags),
        "raw_payload_retained": False,
        "full_option_chain_retained": False,
        "sockjs_frames_retained": False,
    }
    path = Path(root) / "mis_conversational_resolution_diagnostic.json"
    path.write_text(json.dumps(diagnostic, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return diagnostic

def run(text: str, root: str, *, execution_time_utc: str | None = None, resolver: Any | None = None) -> dict[str, Any]:
    root = safe_root(root)
    now = execution_time_utc or utc_now()
    intent = parse_derivatives_intent(text)
    if intent.get("clarification_required"):
        raise SystemExit("clarification_required:" + str(intent.get("clarification_reason")))
    resolver = resolver or CompositeReferenceUniverseProvider(TaifexMisCurrentUniverseProvider(), openapi_reference_fetcher=openapi_tx_reference)
    resolution = resolve_current_contracts(intent, resolver, now_utc=now)
    Path(root).mkdir(parents=True, exist_ok=True)
    (Path(root)/"derivatives_intent.json").write_text(json.dumps(intent, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    (Path(root)/"derivatives_resolution_record.json").write_text(json.dumps(resolution, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    if resolution.get("resolution_status") == "exact_contract_unavailable" or not resolution.get("resolved_exact_targets"):
        diagnostic = write_mis_diagnostic(root, resolver, resolution, operation_results=[], ai_state={"status":"not_run", "package_id": None, "reason": resolution.get("resolution_status")})
        return {"status":"blocked", "resolution": resolution, "ai_package_id": None, "diagnostic": diagnostic}
    sources = ["TAIFEX_MIS", "TAIFEX_OPENAPI"]
    contexts = ["liveish_observation", "official_eod_reference"]
    request = {"schema_version": REQUEST_SCHEMA_VERSION, "request_id": "m8r-f2-conversational", "requested_context_types":contexts, "requested_source_families":sources, "targets":[_target(t, sources) for t in resolution["resolved_exact_targets"]], "output_policy":{"artifact_root": root}}
    plan = compile_market_context_execution_plan(request, created_at_utc=now)
    approval = build_approval_artifact(plan, approved_at_utc=now, single_use=True)
    result = execute_approved_market_context_plan(plan, approval, allow_network=True, execution_time_utc=now, approval_consumption_store=FilesystemApprovalConsumptionStore(root), artifact_writer=lambda **kw: write_execution_artifacts(**kw, artifact_root=plan["output_scope"]["artifact_root"]))
    result["conversation_resolution"] = conversation_resolution_projection(resolution)
    try:
        pkg = build_ai_market_context_package(result, generated_at_utc=now)
        validate_ai_market_context_package(pkg)
        paths = write_ai_market_context_artifacts(pkg, artifact_root=root, receipt_id=result["execution_receipt"]["receipt_id"], allow_existing_receipt_directory=True)
        ai_state = {"status": pkg.get("package_status"), "package_id": pkg.get("package_id"), "reason": None}
        diagnostic = write_mis_diagnostic(root, resolver, resolution, operation_results=result.get("operation_results", []), ai_state=ai_state)
        return {"status":"ready" if pkg.get("package_status") in {"ready", "ready_with_caveats", "partial"} else "blocked", "resolution": resolution, "ai_package_id": pkg.get("package_id"), "ai_package_status": pkg.get("package_status"), "artifact_paths": paths, "operation_results": result.get("operation_results", []), "diagnostic": diagnostic}
    except AIMarketContextPackageError as exc:
        ai_state = {"status": "build_failed", "package_id": None, "reason": str(exc)}
        diagnostic = write_mis_diagnostic(root, resolver, resolution, operation_results=result.get("operation_results", []), ai_state=ai_state)
        return {"status":"blocked", "resolution": resolution, "ai_package_id": None, "ai_package_status": "build_failed", "ai_validation": {"valid": False, "reason_code": str(exc)}, "operation_results": result.get("operation_results", []), "diagnostic": diagnostic}


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--operator-confirmed", action="store_true")
    ap.add_argument("--allow-network", action="store_true")
    ap.add_argument("--artifact-root", required=True)
    ap.add_argument("--execution-time-utc")
    args=ap.parse_args(argv)
    if not args.operator_confirmed or not args.allow_network:
        raise SystemExit("requires --operator-confirmed and --allow-network")
    out=run(args.text, args.artifact_root, execution_time_utc=args.execution_time_utc)
    print(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
