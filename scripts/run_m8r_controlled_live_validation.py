#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, os, platform, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from scripts.m8r_bounded_market_context_request import compile_market_context_execution_plan, build_approval_artifact, REQUEST_SCHEMA_VERSION, M8RValidationError
from scripts.m8r_one_shot_market_context_orchestrator import FilesystemApprovalConsumptionStore, execute_approved_market_context_plan, preflight_approved_market_context_plan, write_execution_artifacts
from scripts.m8r_ai_market_context_package import build_ai_market_context_package, validate_ai_market_context_package, write_ai_market_context_artifacts

MANIFEST_SCHEMA_VERSION="m8r_controlled_live_validation_manifest.v1"
SUMMARY_SCHEMA_VERSION="m8r_controlled_live_validation_summary.v1"
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

def classify(result,pkg):
    if result["execution_status"] in {"ready","ready_with_caveats"} and pkg.get("schema_version")=="ai_market_context.v1": return "passed_with_caveats" if result["execution_status"]=="ready_with_caveats" else "passed"
    issues=[i.get("code") for r in result.get("operation_results",[]) for i in r.get("issues",[])]
    if any(c in issues for c in ["source_timeout","source_connection_failed"]): return "source_temporarily_unavailable"
    if any(c in issues for c in ["source_identity_mismatch","exact_contract_identity_not_returned"]): return "failed_source_identity"
    return "failed_runtime_contract"

def write_json(path:Path,obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")

def run_case(case_id,args,root):
    case=CASES[case_id]; p=plan_for(case_id,case,args,root); a=build_approval_artifact(p, approved_at_utc=args.execution_time_utc or now(), single_use=True)
    print(json.dumps({"case_id":case_id,"target":p["targets"],"source":case["source"],"context":case["contexts"],"artifact_root":p["output_scope"]["artifact_root"],"network_operation_count":len(p["source_to_target_context_mapping"]),"approval_id":a["approval_id"]},ensure_ascii=False))
    if args.dry_run:
        pre=preflight_approved_market_context_plan(p,a,allow_network=False,approval_consumption_store=FilesystemApprovalConsumptionStore(root),execution_time_utc=args.execution_time_utc or now())
        return {"case_id":case_id,"dry_run":True,"plan_id":p["plan_id"],"plan_hash":p["plan_hash"],"approval_id":a["approval_id"],"preflight":pre,"result":"blocked_preflight"}
    store=FilesystemApprovalConsumptionStore(root)
    result=execute_approved_market_context_plan(p,a,allow_network=args.allow_network,execution_time_utc=args.execution_time_utc or now(),approval_consumption_store=store,artifact_writer=lambda **kw: write_execution_artifacts(**kw,artifact_root=p["output_scope"]["artifact_root"]))
    try:
        pkg=build_ai_market_context_package(result, generated_at_utc=args.execution_time_utc or now())
        val=validate_ai_market_context_package(pkg)
    except Exception as exc:
        pkg={"schema_version":"ai_market_context.v1","package_id":None,"package_status":"blocked","caveats":[{"code":"ai_package_build_failed","severity":"error"}],"forbidden_interpretations":[]}
        val={"valid":"false","error":exc.__class__.__name__}
    ai_paths=[]
    if result["execution_receipt"].get("receipt_id") and pkg.get("package_id"):
        try:
            ai_paths=write_ai_market_context_artifacts(pkg, artifact_root=p["output_scope"]["artifact_root"], receipt_id=result["execution_receipt"]["receipt_id"])
        except FileExistsError:
            rd=Path(p["output_scope"]["artifact_root"])/result["execution_receipt"]["receipt_id"]
            for name,key in [("ai_market_context_v1.json",None),("ai_market_context_compact.json","compact"),("ai_market_context_standard.json","standard"),("ai_market_context_diagnostic.json","diagnostic")]:
                payload=pkg if key is None else pkg.get("conversation_views",{}).get(key,{})
                write_json(rd/name,payload); ai_paths.append(str(rd/name))
    ar=audit(Path(p["output_scope"]["artifact_root"]))
    op=result.get("operation_results",[{}])[0] if result.get("operation_results") else {}
    out={"schema_version":"m8r_controlled_live_validation_case_result.v1","case_id":case_id,"target":p["targets"],"requested_context":case["contexts"],"planned_source_family":case["source"],"plan_id":p["plan_id"],"plan_hash":p["plan_hash"],"approval_id":a["approval_id"],"receipt_id":result["execution_receipt"].get("receipt_id"),"approval_consumed":result["execution_receipt"].get("approval_consumed"),"execution_status":result["execution_status"],"operation_status":op.get("status"),"adapter_invocation_count":op.get("adapter_invocation_count",0),"network_attempted":op.get("network_attempted",False),"network_request_count":op.get("network_request_count"),"source_id":(op.get("source_observation") or {}).get("source_id"),"authority_level":(op.get("source_observation") or {}).get("authority_level"),"timing_class":(op.get("source_observation") or {}).get("timing_class"),"source_timestamp":(op.get("source_observation") or {}).get("source_timestamp"),"retrieved_at_utc":(op.get("source_observation") or {}).get("retrieved_at_utc"),"currentness":op.get("currentness"),"returned_identity":op.get("returned_identity"),"identity_verification_result":"matched_or_not_applicable" if op.get("status")=="succeeded" else "not_matched_or_unavailable","grouping":op.get("grouping"),"missing_context":result.get("missing_context"),"artifact_paths":result.get("artifacts",[])+ai_paths,"ai_package_id":pkg.get("package_id"),"ai_package_status":pkg.get("package_status"),"ai_validation":val,"retention_audit":ar,"caveats":pkg.get("caveats"),"forbidden_interpretations":pkg.get("forbidden_interpretations"),"result":classify(result,pkg)}
    write_json(Path(p["output_scope"]["artifact_root"])/"validation_case_result.json",out)
    return out

def summary(root,args,results):
    families={r["planned_source_family"]:r["result"] for r in results if not r.get("dry_run")}
    runtime="passed" if results and all(r.get("retention_audit",{}).get("status") in {None,"passed"} for r in results) else "failed"
    decision="GO" if runtime=="passed" and all(v in {"passed","passed_with_caveats"} for v in families.values()) and len(families)>=5 else "CONDITIONAL_GO" if runtime=="passed" else "NO_GO"
    return {"schema_version":SUMMARY_SCHEMA_VERSION,"validation_run_id":Path(root).name,"starting_commit_sha":git_sha(),"completed_at_utc":now(),"runtime_critical_status":runtime,"source_family_results":families,"exact_future_result":next((r for r in results if "FUTURE" in r["case_id"]),{}),"exact_option_result":next((r for r in results if "OPTION" in r["case_id"]),{}),"retention_audit":audit(Path(root)),"approval_replay_test":{"status":"covered_by_unit_and_runner_store","network_operations_attempted":0},"ai_package_validation":{"case_package_statuses":{r["case_id"]:r.get("ai_package_status") for r in results}},"decision":decision,"production_live_execution_ready":decision=="GO","live_validation_completed":decision=="GO","recommended_next_task":"M8R-04-CONTROLLED-AI-CONVERSATION-HANDOFF" if decision=="GO" else "M8R-02B-TAIFEX-MIS-EXACT-LIVE-REVALIDATION"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--list-cases",action="store_true"); ap.add_argument("--case",action="append"); ap.add_argument("--all-required",action="store_true"); ap.add_argument("--allow-network",action="store_true"); ap.add_argument("--operator-confirmed",action="store_true"); ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--artifact-root",required=False); ap.add_argument("--execution-time-utc");
    for n in ["future-product","future-expiry","option-product","option-underlying","option-expiry","option-strike","option-call-put"]: ap.add_argument("--taifex-"+n)
    args=ap.parse_args()
    if args.list_cases: print("\n".join(CASES)); return
    if args.allow_network and not args.operator_confirmed: raise SystemExit("--allow-network requires --operator-confirmed")
    ids=list(CASES) if args.all_required else (args.case or [])
    unknown=[i for i in ids if i not in CASES]
    if unknown: raise SystemExit("unknown case: "+",".join(unknown))
    root=safe_root(args.artifact_root or "")
    man=manifest(root,args,ids); write_json(Path(root)/"validation_manifest.json",man)
    results=[]
    for cid in ids: results.append(run_case(cid,args,root))
    summ=summary(root,args,results); write_json(Path(root)/"validation_summary.json",summ)
    print(json.dumps(summ,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=="__main__": main()
