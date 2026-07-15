from __future__ import annotations

import json, os, tempfile
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8r_bounded_market_context_request import (
    APPROVAL_SCHEMA_VERSION, PLAN_SCHEMA_VERSION,
    accepted_source_families, canonical_json,
    load_source_registry, sha256_json, validate_approval_for_plan,
    validate_plan_internal_consistency, validate_output_scope,
)

RECEIPT_SCHEMA_VERSION = "m8r_market_context_execution_receipt.v1"
RESULT_SCHEMA_VERSION = "m8r_market_context_orchestration_result.v1"
PREFLIGHT_SCHEMA_VERSION = "m8r_market_context_execution_preflight.v1"
OPERATION_RESULT_SCHEMA_VERSION = "m8r_market_context_operation_result.v1"
MISSING_CONTEXT_SCHEMA_VERSION = "m8r_market_context_missing_context.v1"
SAFE_SOURCES = {"TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI"}
TERMINAL = {"succeeded","failed","blocked","skipped_due_to_dependency"}
NETWORK_CLASS = "planned_network_fetch"
LOCAL_CLASSES = {"local_source_health_read", "local_market_clock_evaluation"}

class M8ROrchestrationError(RuntimeError):
    pass

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def _issue(code: str, message: str, **extra: Any) -> dict[str, Any]:
    out={"code":code,"message":message}
    out.update({k:v for k,v in extra.items() if v is not None})
    return out


def _op_key(op: dict[str, Any]) -> tuple[str, str | None]:
    return (op.get("operation_class"), op.get("source_family"))

def _operation_id(index: int, op: dict[str, Any]) -> str:
    seed={"i":index,"target_id":op.get("target_id"),"context_type":op.get("context_type"),"source_family":op.get("source_family"),"operation_class":op.get("operation_class"),"route":op.get("route")}
    return "m8r-op-"+sha256_json(seed)[:16]

def _target_by_id(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {t.get("target_id"):t for t in plan.get("targets",[]) if isinstance(t,dict)}

def _has_derivative_exact_identity(op: dict[str, Any], target: dict[str, Any] | None) -> bool:
    if op.get("source_family") not in {"TAIFEX_MIS","TAIFEX_OPENAPI"}: return True
    if not target: return False
    ident=target.get("derivative_identity") or {}
    typ=target.get("instrument_type")
    if typ == "future":
        return bool(target.get("symbol") and ident.get("expiry") and ident.get("contract_type") == "monthly" and ident.get("session") == "regular")
    if typ == "option":
        return bool(ident.get("underlying") and ident.get("expiry") and ident.get("strike") and ident.get("call_put") in {"C","P","CALL","PUT"} and ident.get("contract_type") == "monthly" and ident.get("session") == "regular")
    return True

def _executor_supports_exact(executor: Callable[..., Any]) -> bool:
    return bool(getattr(executor, "supports_exact_derivative_identity", False))

def _is_safe_output_scope(scope: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    _norm, issues = validate_output_scope(scope)
    root=(scope or {}).get("artifact_root")
    if not isinstance(root,str) or _norm.get("artifact_root") != str(PurePosixPath(root)):
        issues.append(_issue("unsafe_output_scope","output_scope artifact_root must be normalized relative path"))
    return not issues, issues

def preflight_approved_market_context_plan(plan: dict[str, Any], approval: dict[str, Any], *, executor_registry: Mapping[tuple[str, str | None], Callable[..., Any]] | None = None, execution_time_utc: str | None = None, allow_network: bool = False, source_registry: dict[str, Any] | None = None) -> dict[str, Any]:
    now=execution_time_utc or utc_now(); issues=[]; operations=plan.get("source_to_target_context_mapping") if isinstance(plan,dict) else None
    if not isinstance(plan,dict) or plan.get("schema_version") != PLAN_SCHEMA_VERSION: issues.append(_issue("invalid_plan","plan schema mismatch"))
    else:
        cons=validate_plan_internal_consistency(plan); issues.extend(cons.get("issues",[]))
        if cons.get("rebuilt_hash") and plan.get("plan_hash") != cons.get("rebuilt_hash"): issues.append(_issue("plan_hash_mismatch","plan hash mismatch"))
    if not isinstance(approval,dict) or approval.get("schema_version") != APPROVAL_SCHEMA_VERSION: issues.append(_issue("invalid_approval","approval schema mismatch"))
    elif isinstance(plan,dict):
        issues.extend(validate_approval_for_plan(approval, plan, now_utc=now).get("issues",[]))
        if approval.get("approval_status") == "consumed": issues.append(_issue("approval_consumed","single-use approval already consumed"))
    if not isinstance(operations,list): issues.append(_issue("invalid_plan","source_to_target_context_mapping must be list")); operations=[]
    if len(operations) > 40: issues.append(_issue("operation_limit_exceeded","operation count exceeds M8R bounds"))
    if isinstance(plan,dict) and len(plan.get("targets",[]) or []) > 10: issues.append(_issue("target_limit_exceeded","target count exceeds M8R bounds"))
    sources=set(plan.get("planned_source_families",[]) or []) if isinstance(plan,dict) else set()
    accepted=set(accepted_source_families(source_registry))
    for s in sources:
        if s not in SAFE_SOURCES or s not in accepted: issues.append(_issue("source_not_runtime_eligible","source outside M8R allowlist", source_family=s))
    ok_scope, scope_issues = _is_safe_output_scope((plan or {}).get("output_scope",{})); issues.extend(scope_issues)
    has_network=any(bool(op.get("network_required")) or op.get("operation_class")==NETWORK_CLASS for op in operations)
    if has_network and not allow_network: issues.append(_issue("network_execution_not_enabled","allow_network=true is required for network operations"))
    registry=executor_registry or EXECUTOR_REGISTRY
    targets=_target_by_id(plan if isinstance(plan,dict) else {})
    for op in operations:
        key=_op_key(op)
        executor=registry.get(key)
        if not executor: issues.append(_issue("executor_not_registered","no registered executor for operation/source", operation_class=key[0], source_family=key[1])); continue
        target=targets.get(op.get("target_id"))
        if op.get("source_family") in {"TAIFEX_MIS","TAIFEX_OPENAPI"}:
            if not _has_derivative_exact_identity(op,target): issues.append(_issue("executor_exact_identity_not_supported","approved derivative identity is incomplete", target_id=op.get("target_id")))
            elif not _executor_supports_exact(executor): issues.append(_issue("executor_exact_identity_not_supported","executor does not declare exact derivative identity support", target_id=op.get("target_id"), source_family=op.get("source_family")))
    return {"schema_version":PREFLIGHT_SCHEMA_VERSION,"preflight_status":"passed" if not issues else "blocked","execution_time_utc":now,"allow_network":allow_network,"network_required":has_network,"operation_count":len(operations),"issues":issues,"network_operations_attempted":0}

def normalize_operation_result(raw: Any, op: dict[str, Any], operation_id: str, *, started_at_utc: str, finished_at_utc: str) -> dict[str, Any]:
    raw = raw if isinstance(raw,dict) else {"status":"failed","issues":[{"code":"source_payload_invalid","message":"executor returned non-object"}]}
    status=raw.get("status") or raw.get("operation_status") or ("succeeded" if raw.get("source_observation") or raw.get("observations") else "failed")
    if status not in TERMINAL: status="failed"
    obs=raw.get("source_observation") or (raw.get("observations") or [None])[0]
    return {"schema_version":OPERATION_RESULT_SCHEMA_VERSION,"operation_id":operation_id,"target_id":op.get("target_id"),"context_type":op.get("context_type"),"source_family":op.get("source_family"),"operation_class":op.get("operation_class"),"route":op.get("route"),"status":status,"started_at_utc":started_at_utc,"finished_at_utc":finished_at_utc,"network_attempted":bool(raw.get("network_attempted", op.get("network_required", False) and status != "blocked")),"adapter_invocation_count":int(raw.get("adapter_invocation_count",1)),"source_observation":obs if isinstance(obs,dict) else {},"source_health":raw.get("source_health") or {},"currentness":raw.get("currentness") or (obs or {}).get("currentness") or {},"returned_identity":raw.get("returned_identity") or (obs or {}).get("safe_fields",{}).get("contract_identity") or {},"issues":raw.get("issues") or [],"retained_artifacts":raw.get("retained_artifacts") or [],"grouping":raw.get("grouping") or {"grouped":False}}

def _identity_matches(target: dict[str, Any], result: dict[str, Any]) -> bool:
    if result.get("source_family") not in {"TAIFEX_MIS","TAIFEX_OPENAPI"}: return True
    ident=target.get("derivative_identity") or {}; returned=result.get("returned_identity") or {}
    if target.get("instrument_type") == "future":
        return (returned.get("expiry") == ident.get("expiry") or returned.get("contract_month_or_week") == ident.get("expiry")) and (returned.get("contract_type", ident.get("contract_type")) == ident.get("contract_type"))
    if target.get("instrument_type") == "option":
        return (returned.get("expiry") == ident.get("expiry") or returned.get("contract_month_or_week") == ident.get("expiry")) and str(returned.get("strike") or returned.get("strike_price")) == str(ident.get("strike")) and (returned.get("call_put") or returned.get("option_type"," ")[:1].upper()) == ident.get("call_put")[:1]
    return True

def build_missing_context_records(plan: dict[str, Any], operation_results: list[dict[str, Any]], *, global_reason: str | None = None) -> list[dict[str, Any]]:
    missing=[]
    if global_reason:
        ops=plan.get("source_to_target_context_mapping",[]) if isinstance(plan,dict) else []
        for op in ops:
            missing.append({"schema_version":MISSING_CONTEXT_SCHEMA_VERSION,"target_id":op.get("target_id"),"context_type":op.get("context_type"),"planned_source_family":op.get("source_family"),"missing_context_status":"missing","reason_code":global_reason,"operation_status":"blocked","usable_fallback":None,"forbidden_interpretations":[]})
        return missing
    for r in operation_results:
        if r.get("status") != "succeeded" or not r.get("source_observation"):
            code=(r.get("issues") or [{}])[0].get("code") or ("source_execution_failed" if r.get("status")=="failed" else "executor_exact_identity_not_supported" if r.get("status")=="blocked" else "source_payload_invalid")
            missing.append({"schema_version":MISSING_CONTEXT_SCHEMA_VERSION,"target_id":r.get("target_id"),"context_type":r.get("context_type"),"planned_source_family":r.get("source_family"),"missing_context_status":"missing","reason_code":code,"operation_status":r.get("status"),"usable_fallback":None,"forbidden_interpretations":[]})
    return missing

def derive_execution_status(operation_results: list[dict[str, Any]], missing_context: list[dict[str, Any]], *, global_blocked: bool=False) -> str:
    if global_blocked: return "blocked"
    usable=sum(1 for r in operation_results if r.get("status")=="succeeded" and r.get("source_observation"))
    if usable == 0: return "blocked"
    if missing_context: return "partial"
    if any(r.get("issues") or r.get("currentness") for r in operation_results): return "ready_with_caveats"
    return "ready"

def _blank_receipt(plan, approval, started, finished, status, missing_count=0, success_count=0, approval_consumed=False, reason=None, operation_results=None):
    operation_results=operation_results or []
    rid="m8r-receipt-"+sha256_json({"plan_id":(plan or {}).get("plan_id"),"plan_hash":(plan or {}).get("plan_hash"),"approval_id":(approval or {}).get("approval_id"),"started":started})[:16]
    return {"schema_version":RECEIPT_SCHEMA_VERSION,"receipt_id":rid,"plan_id":(plan or {}).get("plan_id"),"plan_hash":(plan or {}).get("plan_hash"),"approval_id":(approval or {}).get("approval_id"),"approval_binding":{"plan_id":(approval or {}).get("plan_id"),"plan_hash":(approval or {}).get("plan_hash")},"execution_started_at_utc":started,"execution_finished_at_utc":finished,"one_shot":True,"polling":False,"scheduler":False,"background_execution":False,"auto_retry":False,"approved_target_count":len((plan or {}).get("targets",[]) or []),"approved_operation_count":len((plan or {}).get("source_to_target_context_mapping",[]) or []),"logical_operations":[r.get("operation_id") for r in operation_results],"adapter_invocations":sum(int(r.get("adapter_invocation_count",0)) for r in operation_results),"network_operations_attempted":sum(1 for r in operation_results if r.get("network_attempted")),"network_operations_succeeded":sum(1 for r in operation_results if r.get("network_attempted") and r.get("status")=="succeeded"),"network_operations_failed":sum(1 for r in operation_results if r.get("network_attempted") and r.get("status")=="failed"),"local_operations_attempted":sum(1 for r in operation_results if r.get("operation_class") in LOCAL_CLASSES),"successful_context_count":success_count,"missing_context_count":missing_count,"bounded_retention":True,"full_market_retained_output":False,"raw_payload_retained":False,"package_status":status,"approval_consumed":approval_consumed,"reason":reason,"returned_derivative_identities":[{"operation_id":r.get("operation_id"),"target_id":r.get("target_id"),"returned_identity":r.get("returned_identity")} for r in operation_results if r.get("source_family") in {"TAIFEX_MIS","TAIFEX_OPENAPI"}]}

def build_execution_receipt(plan, approval, operation_results, missing_context, *, started_at_utc, finished_at_utc, package_status, approval_consumed, reason=None):
    success=sum(1 for r in operation_results if r.get("status")=="succeeded" and r.get("source_observation"))
    return _blank_receipt(plan, approval, started_at_utc, finished_at_utc, package_status, len(missing_context), success, approval_consumed, reason, operation_results)

def _consume_approval(approval: dict[str, Any], when: str) -> dict[str, Any]:
    out=dict(approval); out["approval_status"]="consumed"; out["consumed_at_utc"]=when; out["consumption_record"]={"consumed_by":"m8r_one_shot_market_context_orchestrator","consumed_at_utc":when}; return out

def execute_approved_market_context_plan(plan: dict[str, Any], approval: dict[str, Any], *, executor_registry: Mapping[tuple[str, str | None], Callable[..., Any]] | None = None, execution_time_utc: str | None = None, allow_network: bool = False, artifact_writer: Callable[..., Any] | None = None, source_registry: dict[str, Any] | None = None) -> dict[str, Any]:
    started=execution_time_utc or utc_now(); registry=executor_registry or EXECUTOR_REGISTRY; src_reg=source_registry or load_source_registry()
    pre=preflight_approved_market_context_plan(plan, approval, executor_registry=registry, execution_time_utc=started, allow_network=allow_network, source_registry=src_reg)
    if pre["preflight_status"] != "passed":
        reason=(pre.get("issues") or [{}])[0].get("code") or "approval_invalid"; missing=build_missing_context_records(plan, [], global_reason=reason); receipt=_blank_receipt(plan, approval, started, started, "blocked", len(missing), 0, False, reason)
        return {"schema_version":RESULT_SCHEMA_VERSION,"execution_status":"blocked","preflight":pre,"execution_receipt":receipt,"operation_results":[],"missing_context":missing,"m8_context_core":None,"m8_context_core_status":{"status":"not_built","reason":reason},"approval_state":dict(approval),"artifacts":[],"network_operations_attempted":0}
    consumed=_consume_approval(approval, started) if approval.get("single_use", True) else dict(approval)
    results=[]; targets=_target_by_id(plan)
    for i, op in enumerate(plan.get("source_to_target_context_mapping",[])):
        opid=_operation_id(i,op); st=utc_now(); executor=registry[_op_key(op)]
        try:
            raw=executor(operation=op, target=targets.get(op.get("target_id")), plan=plan, execution_time_utc=started, allow_network=allow_network)
            result=normalize_operation_result(raw, op, opid, started_at_utc=st, finished_at_utc=utc_now())
            target=targets.get(op.get("target_id"),{})
            if result["status"] == "succeeded" and not _identity_matches(target,result):
                result["status"]="failed"; result["source_observation"]={}; result["issues"].append(_issue("source_identity_mismatch","returned derivative identity does not match approved target"))
        except (M8ROrchestrationError, ValueError, KeyError) as exc:
            result=normalize_operation_result({"status":"failed","issues":[_issue("source_execution_failed",str(exc), error_class=exc.__class__.__name__)]}, op, opid, started_at_utc=st, finished_at_utc=utc_now())
        results.append(result)
    missing=build_missing_context_records(plan, results)
    observations=[r["source_observation"] for r in results if r.get("status")=="succeeded" and r.get("source_observation")]
    core=build_multi_source_market_context(observations, src_reg, now_utc=started) if observations else None
    status=derive_execution_status(results, missing)
    finished=utc_now(); receipt=build_execution_receipt(plan, approval, results, missing, started_at_utc=started, finished_at_utc=finished, package_status=status, approval_consumed=(consumed.get("approval_status")=="consumed"))
    artifacts=[]
    if artifact_writer:
        try: artifacts=artifact_writer(plan=plan, approval=consumed, receipt=receipt, operation_results=results, missing_context=missing, m8_context_core=core) or []
        except OSError as exc: receipt.setdefault("artifact_write_issues",[]).append(_issue("artifact_write_failed",str(exc), error_class=exc.__class__.__name__))
    return {"schema_version":RESULT_SCHEMA_VERSION,"execution_status":status,"preflight":pre,"execution_receipt":receipt,"operation_results":results,"missing_context":missing,"m8_context_core":core,"m8_context_core_status":{"status":"built" if core else "not_built","reason":None if core else "no_usable_context"},"approval_state":consumed,"artifacts":artifacts,"network_operations_attempted":receipt["network_operations_attempted"]}

def write_execution_artifacts(*, plan, approval, receipt, operation_results, missing_context, m8_context_core, artifact_root: str | None = None) -> list[str]:
    scope=plan.get("output_scope",{}); root=artifact_root or scope.get("artifact_root")
    ok, issues=_is_safe_output_scope({"artifact_root":root})
    if not ok: raise OSError("unsafe_output_scope:"+canonical_json(issues))
    run_dir=Path(root)/receipt["receipt_id"]; run_dir.mkdir(parents=True, exist_ok=False)
    payloads={"execution_plan.json":plan,"approval_record.json":approval,"execution_receipt.json":receipt,"operation_results.json":operation_results,"missing_context.json":missing_context,"m8_context_core.json":m8_context_core}
    written=[]
    for name,payload in payloads.items():
        if '"raw_payload":' in canonical_json(payload): raise OSError("raw_payload_retention_forbidden")
        fd,tmp=tempfile.mkstemp(prefix=name, dir=run_dir)
        with os.fdopen(fd,"w",encoding="utf-8") as fh: json.dump(payload, fh, ensure_ascii=False, sort_keys=True, indent=2)
        os.replace(tmp, run_dir/name); written.append(str(run_dir/name))
    return written

# Production default registry is intentionally narrow. Current accepted source executors are
# adapter-shaped in prior milestones; M8R-02 tests inject fake executors. Unsupported live
# wrappers fail closed instead of silently widening scope.
def _blocked_default_executor(*, operation, target, plan, execution_time_utc, allow_network):
    return {"status":"blocked","network_attempted":False,"adapter_invocation_count":0,"issues":[_issue("executor_not_registered","production adapter not wired for one-shot M8R-02; inject accepted executor adapter")]}

def _local_source_health_executor(*, operation, target, plan, execution_time_utc, allow_network):
    return {"status":"succeeded","network_attempted":False,"source_observation":{"source_id":"TWSE_MIS","source_family":"TWSE_MIS","context_type":"source_health","timing_class":"reference_metadata","authority_level":"local_product_surface","retrieved_at_utc":execution_time_utc,"safe_fields":{"artifact_availability":"unknown","staleness_caveat":"local health read is not a live probe"},"caveats":["local source-health context is not current operational proof"]}}

def _local_market_clock_executor(*, operation, target, plan, execution_time_utc, allow_network):
    return {"status":"succeeded","network_attempted":False,"source_observation":{"source_id":"TWSE_MIS","source_family":"TWSE_MIS","context_type":"market_session_state","timing_class":"reference_metadata","authority_level":"local_product_surface","retrieved_at_utc":execution_time_utc,"safe_fields":{"market_session_state":"unresolved","calendar_caveat":"regular-session support only; unresolved fails closed"},"caveats":["market session unresolved unless accepted market-clock artifact provides evidence"]}}

for _f in [_blocked_default_executor]: setattr(_f,"supports_exact_derivative_identity", False)
EXECUTOR_REGISTRY: dict[tuple[str,str|None], Callable[...,Any]] = {
    (NETWORK_CLASS,"TWSE_MIS"):_blocked_default_executor,
    (NETWORK_CLASS,"TWSE_OPENAPI"):_blocked_default_executor,
    (NETWORK_CLASS,"TPEX_OPENAPI"):_blocked_default_executor,
    (NETWORK_CLASS,"TAIFEX_MIS"):_blocked_default_executor,
    (NETWORK_CLASS,"TAIFEX_OPENAPI"):_blocked_default_executor,
    ("local_source_health_read",None):_local_source_health_executor,
    ("local_market_clock_evaluation",None):_local_market_clock_executor,
}
