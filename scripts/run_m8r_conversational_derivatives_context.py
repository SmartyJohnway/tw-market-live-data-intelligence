from __future__ import annotations

import argparse, json, os, sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from typing import Any

from scripts.m8r_derivatives_conversational_intent import parse_derivatives_intent
from scripts.m8r_taifex_current_contract_resolver import TaifexOpenApiUniverseProvider, resolve_current_contracts, utc_now
from scripts.m8r_bounded_market_context_request import REQUEST_SCHEMA_VERSION, build_approval_artifact, compile_market_context_execution_plan
from scripts.m8r_one_shot_market_context_orchestrator import FilesystemApprovalConsumptionStore, execute_approved_market_context_plan, write_execution_artifacts
from scripts.m8r_ai_market_context_package import build_ai_market_context_package, validate_ai_market_context_package, write_ai_market_context_artifacts


def safe_root(root: str) -> str:
    p = PurePosixPath(root)
    if p.is_absolute() or ".." in p.parts or str(p).startswith(("frontend/public", "research/generated")):
        raise SystemExit("artifact-root must be a bounded relative path")
    return str(p)


def _target(t: dict[str, Any], source: str) -> dict[str, Any]:
    if t["instrument_type"] == "future":
        return {"market":"TAIFEX", "instrument_type":"future", "symbol":t["product"], "expiry":t["expiry"], "contract_type":t["contract_type"], "session":t["session"], "requested_source_families":[source], "resolution_mode":"conversational_current"}
    return {"market":"TAIFEX", "instrument_type":"option", "symbol":t["product"], "underlying":t["underlying"], "expiry":t["expiry"], "strike":t["strike"], "call_put":t["call_put"], "contract_type":t["contract_type"], "session":t["session"], "requested_source_families":[source], "resolution_mode":"conversational_current"}


def conversation_resolution_projection(record: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version":"m8r_ai_conversation_resolution.v1", "original_intent_summary": record.get("original_user_text"), "resolved_contracts": record.get("resolved_exact_targets", []), "assumptions": record.get("assumptions", []), "reference_basis": record.get("reference_observation", {}), "contract_resolution_time_utc": record.get("discovered_universe_summary", {}).get("discovered_at_utc") or utc_now(), "reresolution_performed": bool(record.get("reresolution_count")), "reresolution_count": record.get("reresolution_count", 0), "raw_payload_retained": False}


def run(text: str, root: str, *, execution_time_utc: str | None = None) -> dict[str, Any]:
    root = safe_root(root)
    now = execution_time_utc or utc_now()
    intent = parse_derivatives_intent(text)
    if intent.get("clarification_required"):
        raise SystemExit("clarification_required:" + str(intent.get("clarification_reason")))
    resolver = TaifexOpenApiUniverseProvider()
    resolution = resolve_current_contracts(intent, resolver, now_utc=now)
    Path(root).mkdir(parents=True, exist_ok=True)
    (Path(root)/"derivatives_intent.json").write_text(json.dumps(intent, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    (Path(root)/"derivatives_resolution_record.json").write_text(json.dumps(resolution, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    if resolution.get("resolution_status") == "exact_contract_unavailable" or not resolution.get("resolved_exact_targets"):
        return {"status":"blocked", "resolution": resolution, "ai_package_id": None}
    source = "TAIFEX_OPENAPI"
    context_type = "official_eod_reference"
    request = {"schema_version": REQUEST_SCHEMA_VERSION, "request_id": "m8r-f2-conversational", "requested_context_types":[context_type], "requested_source_families":[source], "targets":[_target(t, source) for t in resolution["resolved_exact_targets"]], "output_policy":{"artifact_root": root}}
    plan = compile_market_context_execution_plan(request, created_at_utc=now)
    approval = build_approval_artifact(plan, approved_at_utc=now, single_use=True)
    result = execute_approved_market_context_plan(plan, approval, allow_network=True, execution_time_utc=now, approval_consumption_store=FilesystemApprovalConsumptionStore(root), artifact_writer=lambda **kw: write_execution_artifacts(**kw, artifact_root=plan["output_scope"]["artifact_root"]))
    result["conversation_resolution"] = conversation_resolution_projection(resolution)
    pkg = build_ai_market_context_package(result, generated_at_utc=now)
    validate_ai_market_context_package(pkg)
    paths = write_ai_market_context_artifacts(pkg, artifact_root=root, receipt_id=result["execution_receipt"]["receipt_id"], allow_existing_receipt_directory=True)
    return {"status":"ready" if pkg.get("package_status") in {"ready", "ready_with_caveats", "partial"} else "blocked", "resolution": resolution, "ai_package_id": pkg.get("package_id"), "ai_package_status": pkg.get("package_status"), "artifact_paths": paths, "operation_results": result.get("operation_results", [])}


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
