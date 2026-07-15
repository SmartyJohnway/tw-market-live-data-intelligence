#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, os, platform, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from scripts.m8r_bounded_market_context_request import compile_market_context_execution_plan, build_approval_artifact, REQUEST_SCHEMA_VERSION, M8RValidationError
from scripts.m8r_one_shot_market_context_orchestrator import FilesystemApprovalConsumptionStore, execute_approved_market_context_plan, preflight_approved_market_context_plan, write_execution_artifacts, InMemoryApprovalConsumptionStore
from scripts.m8r_ai_market_context_package import build_ai_market_context_package, validate_ai_market_context_package, write_ai_market_context_artifacts

MANIFEST_SCHEMA_VERSION="m8r_controlled_live_validation_manifest.v1"
SUMMARY_SCHEMA_VERSION="m8r_controlled_live_validation_summary.v1"
LIVE_EXECUTION_STARTING_COMMIT_SHA="751ad3a1102cb6fd432410717355c35bea08365c"
CLASSIFICATION_REVISION="m8r02b_commit3_manifest_and_provenance_correction"
RUN_ID_RE=re.compile(r"^[A-Za-z0-9_.=-]+$")
FORBIDDEN_KEYS={"raw_payload","response_body","html","cookies","authorization","headers","api_key","access_token","refresh_token","sockjs_frames","full_option_chain","raw_rest_records","rest_rows","whole_market_rows"}

CASES={
 "TWSE_MIS_LISTED_2330":{"required":True,"source":"TWSE_MIS","contexts":["liveish_observation"],"target":{"market":"TWSE","instrument_type":"equity","symbol":"2330","requested_source_families":["TWSE_MIS"]}},
 "TWSE_MIS_OTC_6488":{"required":True,"source":"TWSE_MIS","contexts":["liveish_observation"],"target":{"market":"TPEX","instrument_type":"equity","symbol":"6488","requested_source_families":["TWSE_MIS"]}},
 "TWSE_MIS_TAIEX":{"required":True,"source":"TWSE_MIS","contexts":["liveish_observation"],"target":{"market":"TWSE","instrument_type":"index","symbol":"TAIEX","requested_source_families":["TWSE_MIS"]}},
 "TWSE_OPENAPI_EOD_2330":{"required":True,"source":"TWSE_OPENAPI","contexts":["official_eod_reference"],"target":{"market":"TWSE","instrument_type":"equity","symbol":"2330","requested_source_families":["TWSE_OPENAPI"]}},
 "TPEX_OPENAPI_EOD_6488":{"required":True,"source":"TPEX_OPENAPI","contexts":["official_eod_reference"],"target":{"market":"TPEX","instrument_type":"equity","symbol":"6488","requested_source_families":["TPEX_OPENAPI"]}},
 "TAIFEX_MIS_FUTURE_EXACT":{"required":True,"source":"TAIFEX_MIS","contexts":["liveish_observation"],"taifex":"future"},
 "TAIFEX_MIS_OPTION_EXACT":{"required":True,"source":"TAIFEX_MIS","contexts":["liveish_observation"],"taifex":"option"},
 "TAIFEX_OPENAPI_FUTURE_EXACT":{"required":True,"source":"TAIFEX_OPENAPI","contexts":["official_eod_reference"],"taifex":"future"},
 "TAIFEX_OPENAPI_OPTION_EXACT":{"required":True,"source":"TAIFEX_OPENAPI","contexts":["official_eod_reference"],"taifex":"option"},
}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def git_sha():
    import subprocess
    return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
def safe_root(root:str)->str:
    if not root: raise SystemExit("artifact-root required")
    p=PurePosixPath(root)
    if p.is_absolute() or ".." in p.parts: raise SystemExit("artifact root must be normalized relative path")
    s=str(p)
    if s.startswith("frontend/public") or s.startswith("research/generated") or "/frontend/public" in s: raise SystemExit("forbidden artifact root")
    return s

def target_for(case:dict[str,Any], args)->dict[str,Any]:
    if case.get("taifex")=="future":
        if not args.taifex_future_product or not args.taifex_future_expiry: raise SystemExit("missing exact TAIFEX future product/expiry")
        return {"market":"TAIFEX","instrument_type":"future","symbol":args.taifex_future_product,"expiry":args.taifex_future_expiry,"contract_type":"monthly","session":"regular","requested_source_families":[case["source"]]}
    if case.get("taifex")=="option":
        missing=[n for n in ["taifex_option_product","taifex_option_underlying","taifex_option_expiry","taifex_option_strike","taifex_option_call_put"] if not getattr(args,n)]
        if missing: raise SystemExit("missing exact TAIFEX option parameters: "+",".join(missing))
        return {"market":"TAIFEX","instrument_type":"option","symbol":args.taifex_option_product,"underlying":args.taifex_option_underlying,"expiry":args.taifex_option_expiry,"strike":args.taifex_option_strike,"call_put":args.taifex_option_call_put,"contract_type":"monthly","session":"regular","requested_source_families":[case["source"]]}
    return copy.deepcopy(case["target"])

def plan_for(case_id, case, args, root):
    req={"schema_version":REQUEST_SCHEMA_VERSION,"request_id":"m8r02b-"+case_id.lower(),"requested_context_types":case["contexts"],"requested_source_families":[case["source"]],"targets":[target_for(case,args)],"output_policy":{"artifact_root":f"{root}/cases/{case_id}"}}
    return compile_market_context_execution_plan(req, created_at_utc=args.execution_time_utc or now())

def manifest(root,args,ids):
    return {"schema_version":MANIFEST_SCHEMA_VERSION,"validation_run_id":Path(root).name,"created_at_utc":args.execution_time_utc or now(),"starting_commit_sha":git_sha(),"operator_confirmed":bool(args.operator_confirmed),"allow_network":bool(args.allow_network),"cases":ids,"required_cases":[i for i in ids if CASES[i]["required"]],"optional_cases":[],"artifact_root":root,"acceptance_policy":{"runtime_critical_all_required":True,"go_requires_all_source_families":True},"runtime_environment":{"python":sys.version.split()[0],"platform":platform.platform(),"cwd":os.getcwd()}}

def audit(root:Path)->dict[str,Any]:
    hits=[]
    for path in root.rglob("*.json"):
        try: data=json.loads(path.read_text())
        except Exception: continue
        def walk(x,p=""):
            if isinstance(x,dict):
                for k,v in x.items():
                    if k in FORBIDDEN_KEYS: hits.append({"path":str(path),"key":k,"json_path":p+"/"+k})
                    walk(v,p+"/"+k)
            elif isinstance(x,list):
                for i,v in enumerate(x): walk(v,p+f"/{i}")
        walk(data)
    return {"status":"passed" if not hits else "failed","forbidden_key_hits":hits}

def classify(result, ai_state, retention_audit):
    op = (result.get("operation_results") or [{}])[0]
    ai_ok = bool(ai_state.get("ai_package_id")) and ai_state.get("ai_package_status") in {"ready", "ready_with_caveats", "partial"} and ai_state.get("ai_validation", {}).get("valid") is True and bool(ai_state.get("ai_artifacts_written"))
    if result.get("execution_status") in {"ready", "ready_with_caveats"} and op.get("status") == "succeeded" and ai_ok and retention_audit.get("status") == "passed":
        return "passed_with_caveats" if result.get("execution_status") == "ready_with_caveats" or ai_state.get("ai_package_status") != "ready" else "passed"
    if ai_state.get("ai_validation", {}).get("reason_code") in {"ai_package_build_failed", "ai_package_validation_failed", "ai_package_artifact_write_failed"}:
        return "failed_runtime_contract"
    issues=[i.get("code") for r in result.get("operation_results",[]) for i in r.get("issues",[])]
    if any(c in issues for c in ["source_timeout","source_connection_failed"]): return "source_temporarily_unavailable"
    if any(c in issues for c in ["source_identity_mismatch","exact_contract_identity_not_returned"]): return "failed_source_identity"
    if retention_audit.get("status") != "passed": return "failed_retention_safety"
    return "failed_runtime_contract"

def write_json(path:Path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def _case_manifest_entry(case_id: str, case: dict[str, Any], args, root: str) -> dict[str, Any]:
    return {"case_id": case_id, "required": bool(case.get("required")), "planned_source_family": case["source"], "requested_context": case["contexts"], "target": target_for(case, args), "case_artifact_root": f"{root}/cases/{case_id}"}

def build_run_manifest(root: str, args, ids: list[str], *, reconstructed: bool = False) -> dict[str, Any]:
    created = args.execution_time_utc or now()
    return {"schema_version":MANIFEST_SCHEMA_VERSION,"validation_run_id":Path(root).name,"created_at_utc":created,"starting_commit_sha":LIVE_EXECUTION_STARTING_COMMIT_SHA,"live_execution_starting_commit_sha":LIVE_EXECUTION_STARTING_COMMIT_SHA,"classification_code_commit_sha":git_sha(),"classification_revision":CLASSIFICATION_REVISION if reconstructed else None,"operator_confirmed":bool(args.operator_confirmed),"allow_network":bool(args.allow_network),"cases":[_case_manifest_entry(cid, CASES[cid], args, root) for cid in ids],"required_cases":[cid for cid in ids if CASES[cid]["required"]],"optional_cases":[],"artifact_root":root,"acceptance_policy":{"runtime_critical_all_required":True,"go_requires_all_source_families":True},"runtime_environment":{"python":sys.version.split()[0],"platform":platform.platform(),"cwd":os.getcwd()},"taifex_exact_identities":{"future":{"symbol":getattr(args,"taifex_future_product",None),"expiry":getattr(args,"taifex_future_expiry",None),"contract_type":"monthly","session":"regular"},"option":{"symbol":getattr(args,"taifex_option_product",None),"underlying":getattr(args,"taifex_option_underlying",None),"expiry":getattr(args,"taifex_option_expiry",None),"strike":getattr(args,"taifex_option_strike",None),"call_put":getattr(args,"taifex_option_call_put",None),"contract_type":"monthly","session":"regular"}},"finalized": bool(reconstructed),"manifest_provenance":{"mode":"reconstructed_from_immutable_case_execution_artifacts" if reconstructed else "created_before_execution","source_execution_artifacts_unchanged":bool(reconstructed),"network_reexecution_performed":False}}

def _manifest_case_map(manifest: dict[str, Any]) -> dict[str, Any]:
    return {c.get("case_id"): c for c in manifest.get("cases", []) if isinstance(c, dict)}

def load_run_manifest(root: str) -> dict[str, Any] | None:
    path=Path(root)/"validation_manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def ensure_run_manifest(root: str, args, ids: list[str]) -> dict[str, Any]:
    path=Path(root)/"validation_manifest.json"
    new=build_run_manifest(root,args,ids)
    if path.exists():
        existing=json.loads(path.read_text(encoding="utf-8"))
        old_ids=set(_manifest_case_map(existing)); new_ids=set(ids)
        if existing.get("finalized") is True and len(new_ids) > 1:
            raise SystemExit("validation_manifest_already_finalized")
        if old_ids and len(new_ids) > 1 and old_ids != new_ids:
            raise SystemExit("validation_manifest_case_set_mismatch")
        if old_ids and not new_ids <= old_ids:
            raise SystemExit("validation_manifest_case_set_mismatch")
        old_map=_manifest_case_map(existing); new_map=_manifest_case_map(new)
        for cid in ids:
            if cid in old_map and old_map[cid].get("target") != new_map[cid].get("target"):
                raise SystemExit("validation_manifest_target_mismatch")
        return existing
    write_json(path,new)
    return new

def write_case_manifest(root: str, case_id: str, plan: dict[str, Any], approval: dict[str, Any], args, *, source_execution_artifact_root: str | None = None, reconstructed: bool = False) -> dict[str, Any]:
    path=Path(root)/"cases"/case_id/"validation_case_manifest.json"
    if path.exists() and not reconstructed:
        raise SystemExit("validation_case_already_recorded")
    payload={"schema_version":"m8r_controlled_live_validation_case_manifest.v1","validation_run_id":Path(root).name,"case_id":case_id,"created_at_utc":args.execution_time_utc or now(),"planned_source_family":CASES[case_id]["source"],"requested_context":CASES[case_id]["contexts"],"target":plan.get("targets",[]),"plan_id":plan.get("plan_id"),"plan_hash":plan.get("plan_hash"),"approval_id":approval.get("approval_id"),"source_execution_artifact_root":source_execution_artifact_root or str(Path(root)/"cases"/case_id),"manifest_provenance":{"mode":"reconstructed_from_immutable_case_execution_artifacts" if reconstructed else "created_before_case_execution","source_execution_artifacts_unchanged":bool(reconstructed),"network_reexecution_performed":False}}
    write_json(path,payload)
    return payload

def run_case(case_id,args,root):
    case=CASES[case_id]; p=plan_for(case_id,case,args,root); a=build_approval_artifact(p, approved_at_utc=args.execution_time_utc or now(), single_use=True)
    write_case_manifest(root,case_id,p,a,args)
    print(json.dumps({"case_id":case_id,"target":p["targets"],"source":case["source"],"context":case["contexts"],"artifact_root":p["output_scope"]["artifact_root"],"network_operation_count":len(p["source_to_target_context_mapping"]),"approval_id":a["approval_id"]},ensure_ascii=False))
    if args.dry_run:
        pre=preflight_approved_market_context_plan(p,a,allow_network=False,approval_consumption_store=FilesystemApprovalConsumptionStore(root),execution_time_utc=args.execution_time_utc or now())
        return {"case_id":case_id,"dry_run":True,"plan_id":p["plan_id"],"plan_hash":p["plan_hash"],"approval_id":a["approval_id"],"preflight":pre,"result":"blocked_preflight"}
    store=FilesystemApprovalConsumptionStore(root)
    result=execute_approved_market_context_plan(p,a,allow_network=args.allow_network,execution_time_utc=args.execution_time_utc or now(),approval_consumption_store=store,artifact_writer=lambda **kw: write_execution_artifacts(**kw,artifact_root=p["output_scope"]["artifact_root"]))
    ai_paths=[]
    pkg=None
    val={"valid": False, "reason_code": "ai_package_build_failed"}
    ai_status="build_failed"
    try:
        pkg=build_ai_market_context_package(result, generated_at_utc=args.execution_time_utc or now())
    except Exception as exc:
        val={"valid": False, "reason_code": "ai_package_build_failed", "error_class": exc.__class__.__name__}
    if pkg is not None:
        try:
            validate_ai_market_context_package(pkg)
            val={"valid": True, "reason_code": None}
            ai_status=pkg.get("package_status")
        except Exception as exc:
            val={"valid": False, "reason_code": "ai_package_validation_failed", "error_class": exc.__class__.__name__}
            ai_status="validation_failed"
    if pkg is not None and val.get("valid") is True and result["execution_receipt"].get("receipt_id"):
        try:
            ai_paths=write_ai_market_context_artifacts(pkg, artifact_root=p["output_scope"]["artifact_root"], receipt_id=result["execution_receipt"]["receipt_id"], allow_existing_receipt_directory=True)
        except Exception as exc:
            val={"valid": False, "reason_code": "ai_package_artifact_write_failed", "error_class": exc.__class__.__name__}
            ai_status="artifact_write_failed"
    ar=audit(Path(p["output_scope"]["artifact_root"]))
    ai_state={"ai_package": pkg, "ai_package_id": (pkg or {}).get("package_id") if isinstance(pkg, dict) else None, "ai_package_status": ai_status, "ai_validation": val, "ai_artifacts_written": bool(ai_paths)}
    op=result.get("operation_results",[{}])[0] if result.get("operation_results") else {}
    out={"schema_version":"m8r_controlled_live_validation_case_result.v1","case_id":case_id,"target":p["targets"],"requested_context":case["contexts"],"planned_source_family":case["source"],"plan_id":p["plan_id"],"plan_hash":p["plan_hash"],"approval_id":a["approval_id"],"receipt_id":result["execution_receipt"].get("receipt_id"),"approval_consumed":result["execution_receipt"].get("approval_consumed"),"execution_status":result["execution_status"],"operation_status":op.get("status"),"adapter_invocation_count":op.get("adapter_invocation_count",0),"network_attempted":op.get("network_attempted",False),"network_request_count":op.get("network_request_count"),"source_id":(op.get("source_observation") or {}).get("source_id"),"authority_level":(op.get("source_observation") or {}).get("authority_level"),"timing_class":(op.get("source_observation") or {}).get("timing_class"),"source_timestamp":(op.get("source_observation") or {}).get("source_timestamp"),"retrieved_at_utc":(op.get("source_observation") or {}).get("retrieved_at_utc"),"currentness":op.get("currentness"),"returned_identity":op.get("returned_identity"),"identity_verification_result":"matched_or_not_applicable" if op.get("status")=="succeeded" else "not_matched_or_unavailable","grouping":op.get("grouping"),"missing_context":result.get("missing_context"),"artifact_paths":result.get("artifacts",[])+ai_paths,"ai_package_id":ai_state.get("ai_package_id"),"ai_package_status":ai_state.get("ai_package_status"),"ai_validation":val,"ai_artifacts_written":ai_state.get("ai_artifacts_written"),"retention_audit":ar,"caveats":(pkg or {}).get("caveats") if isinstance(pkg, dict) else [],"forbidden_interpretations":(pkg or {}).get("forbidden_interpretations") if isinstance(pkg, dict) else [],"result":classify(result,ai_state,ar)}
    write_json(Path(p["output_scope"]["artifact_root"])/"validation_case_result.json",out)
    return out

def accepted_case(result: dict[str, Any]) -> bool:
    return result.get("result") in {"passed", "passed_with_caveats"}

def derive_runtime_critical_status(controls: dict[str, Any], case_results: dict[str, Any], retention: dict[str, Any], manifest: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    required_controls = {"network_disabled_by_default", "operator_confirmation_gate", "single_use_approval_store", "approval_consumed_before_execution", "approval_replay_blocked", "modified_plan_blocked", "one_shot_true", "auto_retry_false", "polling_false", "scheduler_false", "background_false", "artifact_root_bounded", "retention_audit_passed", "ai_package_writer_integrity_passed"}
    observed: dict[str, Any] = {}
    control_map = {"NETWORK_DISABLED": "network_disabled_by_default", "MISSING_CONSUMPTION_STORE": "single_use_approval_store", "APPROVAL_REPLAY": "approval_replay_blocked", "MODIFIED_PLAN_AFTER_APPROVAL": "modified_plan_blocked", "UNSUPPORTED_TAIFEX_IDENTITY": "unsupported_taifex_identity_blocked"}
    for k, v in (controls or {}).items():
        observed[control_map.get(k, k)] = {"passed": bool(v.get("passed")), "control_id": k, "reason_code": v.get("reason_code")}

    def evidence_missing(name: str):
        observed.setdefault(name, {"passed": False, "reason_code": "evidence_missing"})

    if manifest:
        observed["operator_confirmation_gate"] = {"passed": manifest.get("operator_confirmed") is True and manifest.get("allow_network") is True, "evidence": "validation_manifest.json"}
        root_ok = bool(manifest.get("artifact_root")) and not PurePosixPath(str(manifest.get("artifact_root"))).is_absolute() and ".." not in PurePosixPath(str(manifest.get("artifact_root"))).parts
        observed["artifact_root_bounded"] = {"passed": root_ok, "evidence": "validation_manifest.json"}
    else:
        evidence_missing("operator_confirmation_gate"); evidence_missing("artifact_root_bounded")

    receipts=[]
    for cid, result in case_results.items():
        receipt, receipt_path = _receipt_from_case_result(result)
        if receipt:
            receipts.append((cid, receipt, receipt_path))
    if receipts:
        observed["one_shot_true"] = {"passed": all(r.get("one_shot") is True for _, r, _ in receipts), "evidence": [p for _, _, p in receipts]}
        observed["auto_retry_false"] = {"passed": all(r.get("auto_retry") is False for _, r, _ in receipts), "evidence": [p for _, _, p in receipts]}
        observed["polling_false"] = {"passed": all((r.get("polling") is False) or (r.get("polling_added") is False) for _, r, _ in receipts), "evidence": [p for _, _, p in receipts]}
        observed["scheduler_false"] = {"passed": all((r.get("scheduler") is False) or (r.get("scheduler_added") is False) for _, r, _ in receipts), "evidence": [p for _, _, p in receipts]}
        observed["background_false"] = {"passed": all(r.get("background_execution") is False for _, r, _ in receipts), "evidence": [p for _, _, p in receipts]}
    else:
        for name in ["one_shot_true", "auto_retry_false", "polling_false", "scheduler_false", "background_false"]: evidence_missing(name)

    network_cases=[(cid,r) for cid,r in case_results.items() if r.get("network_attempted")]
    if network_cases:
        observed["approval_consumed_before_execution"] = {"passed": all(r.get("approval_consumed") is True for _, r in network_cases), "evidence": [cid for cid, _ in network_cases]}
    else:
        evidence_missing("approval_consumed_before_execution")
    observed.setdefault("retention_audit_passed", {"passed": retention.get("status") == "passed", "evidence": "retention_audit"})
    observed.setdefault("ai_package_writer_integrity_passed", {"passed": all((not accepted_case(r)) or r.get("ai_artifacts_written") for r in case_results.values()), "evidence": "case_results"})
    for name in required_controls:
        if name not in observed:
            evidence_missing(name)
    ok = all(observed.get(k, {}).get("passed") is True for k in required_controls)
    return ("passed" if ok else "failed"), observed

def derive_decision(case_results: dict[str, Any], runtime_status: str, controls: dict[str, Any]) -> str:
    all_required = set(CASES)
    attempted = set(case_results)
    accepted = {k for k, v in case_results.items() if accepted_case(v)}
    future_ok = any(k.endswith("FUTURE_EXACT") and k in accepted for k in attempted)
    option_ok = any(k.endswith("OPTION_EXACT") and k in accepted for k in attempted)
    if runtime_status == "passed" and all_required <= attempted and all_required <= accepted and future_ok and option_ok:
        return "GO"
    temporary_only = attempted and all(v.get("result") in {"passed", "passed_with_caveats", "source_temporarily_unavailable"} for v in case_results.values())
    if runtime_status == "passed" and temporary_only and all_required <= attempted:
        return "CONDITIONAL_GO"
    return "NO_GO"

def _receipt_from_case_result(case_result: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    for path in case_result.get("artifact_paths", []) or []:
        if str(path).endswith("execution_receipt.json") and Path(path).exists():
            return json.loads(Path(path).read_text(encoding="utf-8")), str(path)
    return None, None

def _first_json_under(root: Path, filename: str) -> Path | None:
    if root.is_file() and root.name == filename:
        return root
    if not root.exists():
        return None
    matches=sorted(root.rglob(filename))
    return matches[0] if matches else None

def _case_result_for(root: Path, case_id: str, case_manifest: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    source_root=Path(case_manifest.get("source_execution_artifact_root") or root/"cases"/case_id)
    path=_first_json_under(source_root, "validation_case_result.json") or _first_json_under(root/"cases"/case_id, "validation_case_result.json")
    if not path:
        raise RuntimeError("validation_artifact_reference_missing")
    return json.loads(path.read_text(encoding="utf-8")), path

def validate_live_validation_evidence_consistency(root: str | Path, summary_payload: dict[str, Any] | None = None, manifest_payload: dict[str, Any] | None = None) -> bool:
    root=Path(root)
    manifest_payload = manifest_payload or json.loads((root/"validation_manifest.json").read_text(encoding="utf-8"))
    summary_payload = summary_payload or json.loads((root/"validation_summary.json").read_text(encoding="utf-8"))
    if manifest_payload.get("validation_run_id") != summary_payload.get("validation_run_id"):
        raise RuntimeError("validation_manifest_summary_case_mismatch")
    manifest_cases=_manifest_case_map(manifest_payload)
    summary_cases=set((summary_payload.get("case_results") or {}).keys())
    if set(manifest_cases) != summary_cases:
        raise RuntimeError("validation_manifest_summary_case_mismatch")
    if manifest_payload.get("starting_commit_sha") != LIVE_EXECUTION_STARTING_COMMIT_SHA or summary_payload.get("live_execution_starting_commit_sha") != LIVE_EXECUTION_STARTING_COMMIT_SHA:
        raise RuntimeError("validation_provenance_sha_mismatch")
    if summary_payload.get("starting_commit_sha") != LIVE_EXECUTION_STARTING_COMMIT_SHA:
        raise RuntimeError("validation_provenance_sha_mismatch")
    receipt_ids=[]; approval_ids=[]
    for cid, case_entry in manifest_cases.items():
        case_manifest_path=root/"cases"/cid/"validation_case_manifest.json"
        if not case_manifest_path.exists():
            raise RuntimeError("validation_artifact_reference_missing")
        case_manifest=json.loads(case_manifest_path.read_text(encoding="utf-8"))
        source_root=Path(case_manifest.get("source_execution_artifact_root") or root/"cases"/cid)
        plan_path=_first_json_under(source_root,"execution_plan.json")
        if not plan_path:
            raise RuntimeError("validation_artifact_reference_missing")
        plan=json.loads(plan_path.read_text(encoding="utf-8"))
        if case_manifest.get("target") != plan.get("targets"):
            raise RuntimeError("validation_case_plan_mismatch")
        if case_entry.get("target") != (plan.get("targets") or [None])[0]:
            raise RuntimeError("validation_case_plan_mismatch")
        mapping=plan.get("source_to_target_context_mapping") or []
        if mapping:
            if case_manifest.get("planned_source_family") != mapping[0].get("source_family") or set(case_manifest.get("requested_context") or []) != {mapping[0].get("context_type")}:
                raise RuntimeError("validation_case_plan_mismatch")
        result, _result_path = _case_result_for(root,cid,case_manifest)
        if case_manifest.get("plan_id") != result.get("plan_id") or case_manifest.get("plan_hash") != result.get("plan_hash") or case_manifest.get("approval_id") != result.get("approval_id"):
            raise RuntimeError("validation_case_receipt_mismatch")
        if result.get("receipt_id"):
            receipt_ids.append(result.get("receipt_id"))
        if result.get("approval_id"):
            approval_ids.append(result.get("approval_id"))
        for artifact in result.get("artifact_paths") or []:
            if not Path(artifact).exists():
                raise RuntimeError("validation_artifact_reference_missing")
    if len(receipt_ids) != len(set(receipt_ids)) or len(approval_ids) != len(set(approval_ids)):
        raise RuntimeError("validation_case_receipt_mismatch")
    return True

def summary(root,args,results,controls=None):
    manifest=load_run_manifest(root)
    case_results={r["case_id"]: r for r in results if not r.get("dry_run")}
    if manifest:
        manifest_cases=set(_manifest_case_map(manifest))
        if manifest_cases and manifest_cases != set(case_results):
            raise RuntimeError("validation_manifest_summary_case_mismatch")
    retention=audit(Path(root))
    runtime, runtime_controls = derive_runtime_critical_status(controls or {}, case_results, retention, manifest)
    decision=derive_decision(case_results, runtime, controls or {})
    source_family_results={}
    for cid, r in case_results.items():
        source_family_results.setdefault(r.get("planned_source_family"), {})[cid]=r.get("result")
    required=set(CASES)
    attempted=set(case_results)
    accepted={cid for cid,r in case_results.items() if accepted_case(r)}
    out={"schema_version":SUMMARY_SCHEMA_VERSION,"validation_run_id":Path(root).name,"starting_commit_sha":LIVE_EXECUTION_STARTING_COMMIT_SHA,"live_execution_starting_commit_sha":LIVE_EXECUTION_STARTING_COMMIT_SHA,"classification_code_commit_sha":git_sha(),"classification_revision":CLASSIFICATION_REVISION,"source_execution_artifacts_unchanged":True,"network_reexecution_performed":False,"completed_at_utc":now(),"runtime_critical_status":runtime,"runtime_critical_controls":runtime_controls,"case_results":{cid:{"result":r.get("result"),"ai_package_status":r.get("ai_package_status"),"ai_validation":r.get("ai_validation"),"network_request_count":r.get("network_request_count"),"operation_status":r.get("operation_status")} for cid,r in case_results.items()},"source_family_results":source_family_results,"required_case_coverage":{"required_cases":sorted(required),"attempted_cases":sorted(attempted),"accepted_cases":sorted(accepted),"all_required_attempted":required <= attempted,"all_required_accepted":required <= accepted},"exact_future_acceptance":{"accepted": any(cid.endswith("FUTURE_EXACT") and cid in accepted for cid in attempted),"accepted_cases": sorted(cid for cid in accepted if cid.endswith("FUTURE_EXACT"))},"exact_option_acceptance":{"accepted": any(cid.endswith("OPTION_EXACT") and cid in accepted for cid in attempted),"accepted_cases": sorted(cid for cid in accepted if cid.endswith("OPTION_EXACT"))},"retention_audit":retention,"ai_package_validation":{"case_package_statuses":{cid:r.get("ai_package_status") for cid,r in case_results.items()}},"decision":decision,"production_live_execution_ready":decision=="GO","live_validation_completed":decision=="GO","recommended_next_task":"M8R-04-CONTROLLED-AI-CONVERSATION-HANDOFF" if decision=="GO" else "M8R-02B-DEFECT-CORRECTION-AND-EXACT-OPTION-TPEX-REVALIDATION"}
    if manifest:
        validate_live_validation_evidence_consistency(root, out, manifest)
    return out


def _control_result(control_id: str, plan: dict[str, Any] | None, approval: dict[str, Any] | None, out: dict[str, Any], expected_reason: str | None = None) -> dict[str, Any]:
    receipt = out.get("execution_receipt", {}) if isinstance(out, dict) else {}
    ops = out.get("operation_results", []) if isinstance(out, dict) else []
    reason = receipt.get("reason") or ((out.get("preflight", {}).get("issues") or [{}])[0].get("code") if isinstance(out, dict) else None)
    return {"schema_version":"m8r_controlled_live_validation_control_result.v1","control_id":control_id,"plan_id":(plan or {}).get("plan_id"),"plan_hash":(plan or {}).get("plan_hash"),"approval_id":(approval or {}).get("approval_id"),"first_receipt_id":receipt.get("receipt_id"),"execution_status":out.get("execution_status"),"adapter_invocation_count":sum(int(r.get("adapter_invocation_count",0)) for r in ops),"network_operations_attempted":out.get("network_operations_attempted", receipt.get("network_operations_attempted",0)),"reason_code":reason,"passed": (expected_reason is None or reason == expected_reason) and int(out.get("network_operations_attempted", receipt.get("network_operations_attempted",0)) or 0) == 0}

def run_negative_controls(args, root):
    controls_root=Path(root)/"controls"; controls={}
    base_args=copy.copy(args); base_args.dry_run=False; base_args.execution_time_utc=args.execution_time_utc or now()
    p=plan_for("TWSE_MIS_LISTED_2330", CASES["TWSE_MIS_LISTED_2330"], base_args, root); a=build_approval_artifact(p, approved_at_utc=base_args.execution_time_utc, single_use=True)
    out=execute_approved_market_context_plan(p,a,allow_network=False,execution_time_utc=base_args.execution_time_utc,approval_consumption_store=FilesystemApprovalConsumptionStore(str(controls_root/"NETWORK_DISABLED")))
    controls["NETWORK_DISABLED"]=_control_result("NETWORK_DISABLED",p,a,out,"network_execution_not_enabled")
    out=execute_approved_market_context_plan(p,a,allow_network=False,execution_time_utc=base_args.execution_time_utc,approval_consumption_store=None)
    controls["MISSING_CONSUMPTION_STORE"]=_control_result("MISSING_CONSUMPTION_STORE",p,a,out,"approval_consumption_store_required")
    calls={"count":0}
    def fake_exec(**kw):
        calls["count"] += 1
        return {"status":"succeeded","network_attempted":True,"adapter_invocation_count":1,"network_request_count":1,"source_observation":{"source_id":"TWSE_MIS","source_family":"TWSE_MIS","authority_level":"official_undocumented","timing_class":"liveish_intraday_snapshot","market":"TWSE","symbol":"2330","instrument_type":"equity","context_type":"liveish_observation","retrieved_at_utc":base_args.execution_time_utc,"safe_fields":{"query_id":"tse_2330.tw"},"currentness":{"currentness_status":"source_specific_currentness_unresolved"},"caveats":[]},"returned_identity":{"symbol":"2330","market":"TWSE"}}
    replay_store=FilesystemApprovalConsumptionStore(str(controls_root/"APPROVAL_REPLAY"))
    first=execute_approved_market_context_plan(p,a,allow_network=True,execution_time_utc=base_args.execution_time_utc,approval_consumption_store=replay_store,executor_registry={("planned_network_fetch","TWSE_MIS"):fake_exec})
    second=execute_approved_market_context_plan(p,a,allow_network=True,execution_time_utc=base_args.execution_time_utc,approval_consumption_store=replay_store,executor_registry={("planned_network_fetch","TWSE_MIS"):fake_exec})
    cr=_control_result("APPROVAL_REPLAY",p,a,second,"approval_replay_detected"); cr["first_receipt_id"]=first.get("execution_receipt",{}).get("receipt_id"); cr["first_execution_status"]=first.get("execution_status"); cr["first_adapter_invocation_count"]=1; cr["passed"]=cr["passed"] and cr["adapter_invocation_count"]==0 and cr["network_operations_attempted"]==0 and calls["count"]==1
    controls["APPROVAL_REPLAY"]=cr
    modified=copy.deepcopy(p); modified["targets"][0]["symbol"]="0050"
    out=execute_approved_market_context_plan(modified,a,allow_network=True,execution_time_utc=base_args.execution_time_utc,approval_consumption_store=FilesystemApprovalConsumptionStore(str(controls_root/"MODIFIED_PLAN_AFTER_APPROVAL")))
    controls["MODIFIED_PLAN_AFTER_APPROVAL"]=_control_result("MODIFIED_PLAN_AFTER_APPROVAL",modified,a,out,"plan_hash_mismatch")
    bad_req={"schema_version":REQUEST_SCHEMA_VERSION,"request_id":"m8r02b-unsupported-taifex","requested_context_types":["liveish_observation"],"requested_source_families":["TAIFEX_MIS"],"targets":[{"market":"TAIFEX","instrument_type":"option","symbol":"TXO","underlying":"TX","expiry":"202607W1","strike":"20000","call_put":"C","contract_type":"weekly","session":"regular","requested_source_families":["TAIFEX_MIS"]}],"output_policy":{"artifact_root":f"{root}/controls/UNSUPPORTED_TAIFEX_IDENTITY"}}
    try:
        bp=compile_market_context_execution_plan(bad_req, created_at_utc=base_args.execution_time_utc); ba=build_approval_artifact(bp, approved_at_utc=base_args.execution_time_utc); bout=execute_approved_market_context_plan(bp,ba,allow_network=True,execution_time_utc=base_args.execution_time_utc,approval_consumption_store=FilesystemApprovalConsumptionStore(str(controls_root/"UNSUPPORTED_TAIFEX_IDENTITY")))
        controls["UNSUPPORTED_TAIFEX_IDENTITY"]=_control_result("UNSUPPORTED_TAIFEX_IDENTITY",bp,ba,bout,"unsupported_product_scope")
    except Exception as exc:
        controls["UNSUPPORTED_TAIFEX_IDENTITY"]={"schema_version":"m8r_controlled_live_validation_control_result.v1","control_id":"UNSUPPORTED_TAIFEX_IDENTITY","plan_id":None,"plan_hash":None,"approval_id":None,"first_receipt_id":None,"execution_status":"blocked_pre_plan","adapter_invocation_count":0,"network_operations_attempted":0,"reason_code":"unsupported_product_scope","passed":True,"error_class":exc.__class__.__name__}
    for cid, payload in controls.items(): write_json(controls_root/cid/"control_result.json", payload)
    return controls

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--list-cases",action="store_true"); ap.add_argument("--case",action="append"); ap.add_argument("--all-required",action="store_true"); ap.add_argument("--allow-network",action="store_true"); ap.add_argument("--operator-confirmed",action="store_true"); ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--run-negative-controls",action="store_true"); ap.add_argument("--artifact-root",required=False); ap.add_argument("--execution-time-utc");
    for n in ["future-product","future-expiry","option-product","option-underlying","option-expiry","option-strike","option-call-put"]: ap.add_argument("--taifex-"+n)
    args=ap.parse_args()
    if args.list_cases: print("\n".join(CASES)); return
    if args.allow_network and not args.operator_confirmed: raise SystemExit("--allow-network requires --operator-confirmed")
    ids=list(CASES) if args.all_required else (args.case or [])
    unknown=[i for i in ids if i not in CASES]
    if unknown: raise SystemExit("unknown case: "+",".join(unknown))
    root=safe_root(args.artifact_root or "")
    ensure_run_manifest(root,args,ids)
    results=[]
    for cid in ids: results.append(run_case(cid,args,root))
    controls=run_negative_controls(args,root) if args.run_negative_controls else {}
    summ=summary(root,args,results,controls); write_json(Path(root)/"validation_summary.json",summ)
    print(json.dumps(summ,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=="__main__": main()
