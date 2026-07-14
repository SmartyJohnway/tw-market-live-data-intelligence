from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

REQUEST_SCHEMA_VERSION = "m8r_bounded_market_context_request.v1"
NORMALIZED_SCHEMA_VERSION = "m8r_normalized_market_context_request.v1"
PLAN_SCHEMA_VERSION = "m8r_market_context_execution_plan.v1"
APPROVAL_SCHEMA_VERSION = "m8r_market_context_approval.v1"
REGISTRY_SCHEMA_VERSION = "m8_source_capability_registry.v1"

MAX_TARGETS = 10
MAX_SOURCE_FAMILIES = 5
MAX_CONTEXT_TYPES_PER_TARGET = 5
MAX_TOTAL_TARGET_CONTEXTS = 40
MAX_OUTPUT_RELATIVE_PATH_LENGTH = 160
MAX_IDENTIFIER_LENGTH = 64

CONTEXT_TYPES = {
    "liveish_observation",
    "official_eod_reference",
    "official_statistical_reference",
    "source_health",
    "market_session_state",
}
DEFAULT_CONTEXT_TYPES = ("liveish_observation", "official_eod_reference")
SOURCE_REGISTRY_PATH = "docs/data_capabilities/m8_source_capability_registry.json"

MARKET_ALIASES = {"TWSE":"TWSE","TSE":"TWSE","上市":"TWSE","TPEX":"TPEX","OTC":"TPEX","TPEx":"TPEX","上櫃":"TPEX","TAIFEX":"TAIFEX","期交所":"TAIFEX"}
INSTRUMENT_ALIASES = {"stock":"equity","listed_equity":"equity","listed_or_otc_equity":"equity","equity":"equity","etf":"etf","listed_etf":"etf","index":"index","market_index":"index","future":"future","futures":"future","option":"option","options":"option"}
NON_GOAL_FLAGS = {
    "network_execution": False, "source_adapter_invocation": False, "orchestrator": False,
    "api_surface": False, "mcp_surface": False, "frontend_surface": False,
    "scheduler": False, "polling": False, "background_service": False,
    "auto_retry": False, "database": False, "cache": False,
    "full_market_scanner": False, "ranking": False, "alert": False,
    "prediction": False, "recommendation": False, "broker_execution": False,
    "m9_ingestion": False,
}

class M8RValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]):
        super().__init__("m8r_validation_failed")
        self.issues = issues

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def load_source_registry(path: str = SOURCE_REGISTRY_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)

def _source_map(source_registry: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    reg = source_registry or load_source_registry()
    return {s.get("source_family"): s for s in reg.get("sources", []) if isinstance(s, dict)}

def accepted_source_families(source_registry: dict[str, Any] | None = None) -> tuple[str, ...]:
    sources = _source_map(source_registry)
    accepted=[]
    for fam, s in sources.items():
        if s.get("runtime_available") is True and s.get("runtime_executable") is True and s.get("ai_context_allowed") is True and s.get("credential_required") is False and s.get("source_family") in {"TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI"}:
            accepted.append(fam)
    return tuple(sorted(accepted))

def _issue(code, message, scope="request", target_id=None, field=None):
    d={"code":code,"message":message,"scope":scope}
    if target_id is not None: d["target_id"]=target_id
    if field is not None: d["field"]=field
    return d

def _norm_market(v):
    if not isinstance(v,str): return None
    return MARKET_ALIASES.get(v.strip().upper()) or MARKET_ALIASES.get(v.strip())

def _norm_instr(v):
    if not isinstance(v,str): return None
    return INSTRUMENT_ALIASES.get(v.strip().lower())

def _norm_symbol(v):
    return v.strip().upper() if isinstance(v,str) else None

def validate_output_scope(output_policy: dict[str, Any] | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy = output_policy or {}
    root = policy.get("artifact_root", "research/m8r/planned")
    issues=[]
    if not isinstance(root,str) or not root or len(root)>MAX_OUTPUT_RELATIVE_PATH_LENGTH:
        issues.append(_issue("unsafe_output_scope","artifact_root must be a bounded relative path", field="output_policy.artifact_root"))
        root="research/m8r/planned"
    p=PurePosixPath(root)
    parts=set(p.parts)
    if root.startswith("/") or ".." in parts or any(part in {".env","secrets","credentials"} for part in parts) or str(p).startswith(("frontend/public","research/generated")):
        issues.append(_issue("unsafe_output_scope","artifact_root must not be absolute, traversal, public, generated, or secret-bearing", field="output_policy.artifact_root"))
    return {"artifact_root": str(p), "write_artifacts": False, "raw_payload_retention": False}, issues

def _target_contexts(target, request_contexts):
    return tuple(sorted(target.get("requested_context_types") or request_contexts or DEFAULT_CONTEXT_TYPES))

def _target_sources(target, request_sources, source_registry):
    requested = target.get("requested_source_families") or request_sources
    return tuple(sorted(requested or accepted_source_families(source_registry)))

def _allowed_for_identity(market, typ, target):
    if market == "TWSE" and typ in {"equity","etf"}: return {"liveish_observation":"TWSE_MIS","official_eod_reference":"TWSE_OPENAPI"}, {"TWSE_MIS":"tse_{symbol}.tw","TWSE_OPENAPI":"TWSE_OPENAPI"}
    if market == "TPEX" and typ in {"equity","etf"}: return {"liveish_observation":"TWSE_MIS","official_eod_reference":"TPEX_OPENAPI"}, {"TWSE_MIS":"otc_{symbol}.tw","TPEX_OPENAPI":"TPEX_OPENAPI"}
    if market == "TWSE" and typ == "index": return {"liveish_observation":"TWSE_MIS"}, {"TWSE_MIS":"tse_t00.tw"}
    if market == "TAIFEX" and typ == "future": return {"liveish_observation":"TAIFEX_MIS","official_statistical_reference":"TAIFEX_OPENAPI","official_eod_reference":"TAIFEX_OPENAPI"}, {"TAIFEX_MIS":"regular_session_monthly_future_selector","TAIFEX_OPENAPI":"TAIFEX_OPENAPI"}
    if market == "TAIFEX" and typ == "option": return {"liveish_observation":"TAIFEX_MIS","official_statistical_reference":"TAIFEX_OPENAPI","official_eod_reference":"TAIFEX_OPENAPI"}, {"TAIFEX_MIS":"regular_session_monthly_option_selector","TAIFEX_OPENAPI":"TAIFEX_OPENAPI"}
    return {}, {}

def resolve_target_identity(target: dict[str, Any], *, request_context_types=(), request_source_families=(), source_registry=None) -> dict[str, Any]:
    symbol=_norm_symbol(target.get("symbol")); market=_norm_market(target.get("market")); typ=_norm_instr(target.get("instrument_type")); issues=[]
    raw_id=f"{target.get('market')}:{target.get('instrument_type')}:{target.get('symbol')}"
    if not market: issues.append(_issue("invalid_market","explicit supported market is required","target",raw_id,"market"))
    if not symbol or not re.fullmatch(r"[A-Z0-9._-]{1,20}", symbol): issues.append(_issue("invalid_symbol","bounded symbol is required","target",raw_id,"symbol"))
    if not typ: issues.append(_issue("invalid_instrument_type","explicit supported instrument_type is required","target",raw_id,"instrument_type"))
    if symbol and len(symbol)>MAX_IDENTIFIER_LENGTH: issues.append(_issue("identifier_too_long","symbol too long","target",raw_id,"symbol"))
    if issues: return {"input_identity":target,"target_id":raw_id,"identity_resolution_status":"rejected","issues":issues}
    if market in {"TWSE","TPEX"} and typ in {"future","option"}: issues.append(_issue("instrument_type_market_incompatible","cash market cannot use derivative instrument type","target",raw_id))
    if market == "TAIFEX" and typ in {"equity","etf","index"}: issues.append(_issue("instrument_type_market_incompatible","TAIFEX target must be derivative","target",raw_id))
    if symbol == "TAIEX" and not (market == "TWSE" and typ == "index"): issues.append(_issue("market_symbol_incompatible","TAIEX must be TWSE index","target",raw_id))
    if typ == "index" and symbol != "TAIEX": issues.append(_issue("unresolved_identity","only TAIEX index route is supported in M8R-01","target",raw_id))
    if typ == "option":
        required=("underlying","expiry","strike","call_put","contract_type")
        missing=[k for k in required if not target.get(k)]
        if missing: issues.append(_issue("ambiguous_identity","option identity requires underlying, expiry, strike, call_put, contract_type","target",raw_id))
        if str(target.get("contract_type","")).lower()=="weekly": issues.append(_issue("unsupported_product_scope","weekly option runtime remains deferred","target",raw_id))
    if market == "TAIFEX" and str(target.get("session","regular")).lower() not in {"regular","regular_session"}: issues.append(_issue("unsupported_session_scope","TAIFEX after-hours runtime is not accepted","target",raw_id))
    allowed_by_context, routes = _allowed_for_identity(market, typ, target)
    contexts=_target_contexts(target, request_context_types)
    sources=_target_sources(target, request_source_families, source_registry)
    source_policies=_source_map(source_registry)
    eligible=set(accepted_source_families(source_registry))
    for c in contexts:
        if c not in CONTEXT_TYPES: issues.append(_issue("unsupported_context_type",f"unsupported context type {c}","target",raw_id))
    for s in sources:
        pol=source_policies.get(s)
        if s not in source_policies: issues.append(_issue("unsupported_source_family",f"unsupported source family {s}","target",raw_id))
        elif pol.get("credential_required") is True: issues.append(_issue("credential_gated_source_forbidden",f"credential-gated source forbidden {s}","target",raw_id))
        elif s not in eligible: issues.append(_issue("source_not_runtime_eligible",f"source is not M8R runtime/AI eligible {s}","target",raw_id))
    mappings=[]
    for c in contexts:
        required=allowed_by_context.get(c)
        if c in {"source_health","market_session_state"}: continue
        if not required:
            issues.append(_issue("unsupported_context_type",f"context {c} unsupported for target identity","target",raw_id)); continue
        if required not in sources:
            issues.append(_issue("source_target_incompatible",f"required source {required} not selected for {c}","target",raw_id)); continue
        route=routes[required].replace("{symbol}",symbol.lower() if required=="TWSE_MIS" else symbol)
        mappings.append({"context_type":c,"source_family":required,"operation_class":"planned_network_fetch","route":route})
    target_id=f"{market}:{typ}:{symbol}"
    if typ=="option": target_id += f":{target.get('underlying')}:{target.get('expiry')}:{target.get('strike')}:{str(target.get('call_put')).upper()}:{str(target.get('contract_type')).lower()}"
    return {"input_identity":target,"target_id":target_id,"symbol":symbol,"market":market,"instrument_type":typ,"identity_resolution_status":"rejected" if issues else "resolved","requested_context_types":list(contexts),"requested_source_families":list(sources),"allowed_source_families":sorted(set(allowed_by_context.values())),"runtime_routes":routes,"planned_mappings":mappings,"issues":issues}

def normalize_market_context_request(request: dict[str, Any], *, source_registry=None) -> dict[str, Any]:
    issues=[]
    if not isinstance(request,dict): raise M8RValidationError([_issue("missing_required_field","request must be object")])
    if request.get("schema_version") != REQUEST_SCHEMA_VERSION: issues.append(_issue("invalid_schema_version",f"schema_version must be {REQUEST_SCHEMA_VERSION}",field="schema_version"))
    request_id=str(request.get("request_id") or "m8r-request").strip()
    if not request_id or len(request_id)>MAX_IDENTIFIER_LENGTH: issues.append(_issue("identifier_too_long","request_id is missing or too long",field="request_id"))
    targets=request.get("targets")
    if not isinstance(targets,list) or not targets: issues.append(_issue("missing_required_field","targets must be non-empty",field="targets")); targets=[]
    if len(targets)>MAX_TARGETS: issues.append(_issue("target_limit_exceeded","too many targets",field="targets"))
    req_contexts=tuple(sorted(request.get("requested_context_types") or DEFAULT_CONTEXT_TYPES))
    req_sources=tuple(sorted(request.get("requested_source_families") or accepted_source_families(source_registry)))
    if len(req_contexts)>MAX_CONTEXT_TYPES_PER_TARGET: issues.append(_issue("context_limit_exceeded","too many request context types"))
    if len(req_sources)>MAX_SOURCE_FAMILIES: issues.append(_issue("source_limit_exceeded","too many source families"))
    for c in req_contexts:
        if c not in CONTEXT_TYPES: issues.append(_issue("unsupported_context_type",f"unsupported context type {c}"))
    eligible=set(accepted_source_families(source_registry)); policies=_source_map(source_registry)
    for s in req_sources:
        if s not in policies: issues.append(_issue("unsupported_source_family",f"unsupported source family {s}"))
        elif policies[s].get("credential_required") is True: issues.append(_issue("credential_gated_source_forbidden",f"credential-gated source forbidden {s}"))
        elif s not in eligible: issues.append(_issue("source_not_runtime_eligible",f"source not runtime/AI eligible {s}"))
    output_policy, out_issues=validate_output_scope(request.get("output_policy")); issues.extend(out_issues)
    if issues: raise M8RValidationError(issues)
    resolved=[resolve_target_identity(t, request_context_types=req_contexts, request_source_families=req_sources, source_registry=source_registry) for t in targets]
    seen={}; final=[]; rejected=[]
    for r in sorted(resolved, key=lambda x: x.get("target_id","")):
        if r["target_id"] in seen:
            if canonical_json(seen[r["target_id"]].get("input_identity")) != canonical_json(r.get("input_identity")):
                r["issues"].append(_issue("duplicate_target_conflict","duplicate target has conflicting definition","target",r["target_id"]))
                r["identity_resolution_status"]="rejected"
            else:
                continue
        seen[r["target_id"]]=r
        (final if r["identity_resolution_status"]=="resolved" else rejected).append(r)
    if sum(len(r.get("requested_context_types",[])) for r in final+rejected)>MAX_TOTAL_TARGET_CONTEXTS: raise M8RValidationError([_issue("context_limit_exceeded","too many target-context combinations")])
    return {"schema_version":NORMALIZED_SCHEMA_VERSION,"request_id":request_id,"requested_context_types":list(req_contexts),"requested_source_families":list(req_sources),"execution_policy":{"one_shot":True,"network_execution_in_m8r01":False,"approval_required":True,"auto_retry":False},"output_policy":output_policy,"targets":final,"rejected_targets":rejected,"normalization_warnings":[],"non_goal_flags":dict(sorted(NON_GOAL_FLAGS.items()))}

def validate_market_context_request(request: dict[str, Any], *, source_registry=None) -> dict[str, Any]:
    try:
        n=normalize_market_context_request(request, source_registry=source_registry)
        return {"valid": bool(n["targets"]), "issues": [] if n["targets"] else [_issue("unresolved_identity","at least one resolved target is required")], "normalized_request": n}
    except M8RValidationError as e:
        return {"valid": False, "issues": e.issues, "normalized_request": None}

def compute_plan_hash(plan_or_scope: dict[str, Any]) -> str:
    scope=plan_or_scope.get("hash_scope") if isinstance(plan_or_scope,dict) and "hash_scope" in plan_or_scope else plan_or_scope
    return sha256_json(scope)

def compile_market_context_execution_plan(request_or_normalized: dict[str, Any], *, source_registry=None, created_at_utc: str | None = None) -> dict[str, Any]:
    n = request_or_normalized if request_or_normalized.get("schema_version")==NORMALIZED_SCHEMA_VERSION else normalize_market_context_request(request_or_normalized, source_registry=source_registry)
    if not n["targets"]: raise M8RValidationError([_issue("unresolved_identity","at least one resolved target is required")])
    source_to_target=[]
    for t in n["targets"]:
        for m in t["planned_mappings"]: source_to_target.append({"target_id":t["target_id"], **m})
    scope={"schema_version":PLAN_SCHEMA_VERSION,"normalized_request_hash":sha256_json(n),"targets":[{"target_id":t["target_id"],"market":t["market"],"symbol":t["symbol"],"instrument_type":t["instrument_type"]} for t in n["targets"]],"requested_context_types":n["requested_context_types"],"planned_source_families":sorted({m["source_family"] for m in source_to_target}),"source_to_target_context_mapping":sorted(source_to_target,key=lambda x:(x["target_id"],x["context_type"],x["source_family"])),"network_scope":{"network_required":True,"operation_classes":["planned_network_fetch"],"network_execution_in_m8r01":False},"retained_scope":{"bounded_targets_only":True,"full_market_retained_output":False,"raw_payload_retention":False},"output_scope":n["output_policy"],"approval_required":True,"non_goal_flags":n["non_goal_flags"]}
    h=sha256_json(scope)
    return {"schema_version":PLAN_SCHEMA_VERSION,"plan_id":"m8r-plan-"+h[:16],"plan_hash":h,"normalized_request_hash":scope["normalized_request_hash"],"request_id":n["request_id"],"created_at_utc":created_at_utc or utc_now(),"targets":n["targets"],"rejected_targets":n["rejected_targets"],"requested_context_types":n["requested_context_types"],"planned_source_families":scope["planned_source_families"],"source_to_target_context_mapping":scope["source_to_target_context_mapping"],"network_required":True,"approval_required":True,"bounded_retained_scope":scope["retained_scope"],"output_scope":scope["output_scope"],"non_goal_flags":scope["non_goal_flags"],"hash_scope":scope}

def build_approval_artifact(plan: dict[str, Any], *, approval_status="approved", approved_by="operator", approved_at_utc: str | None = None, expires_at_utc: str | None = None, single_use=True) -> dict[str, Any]:
    h=compute_plan_hash(plan)
    return {"schema_version":APPROVAL_SCHEMA_VERSION,"approval_id":"m8r-approval-"+sha256_json({"plan_id":plan["plan_id"],"plan_hash":h,"approved_by":approved_by})[:16],"plan_id":plan["plan_id"],"plan_hash":h,"approval_status":approval_status,"approved_at_utc":approved_at_utc or utc_now(),"approved_by":approved_by,"single_use":bool(single_use),"expires_at_utc":expires_at_utc,"approved_scope":{"target_ids":[t["target_id"] for t in plan["targets"]],"source_families":plan["planned_source_families"],"context_types":plan["requested_context_types"],"output_scope":plan["output_scope"]}}

def validate_approval_for_plan(approval: dict[str, Any], plan: dict[str, Any], *, now_utc: str | None = None) -> dict[str, Any]:
    issues=[]
    if approval.get("schema_version") != APPROVAL_SCHEMA_VERSION: issues.append(_issue("invalid_schema_version","approval schema mismatch"))
    if approval.get("approval_status") != "approved": issues.append(_issue("approval_not_approved","approval status is not approved"))
    if approval.get("plan_id") != plan.get("plan_id"): issues.append(_issue("approval_plan_mismatch","approval plan_id mismatch"))
    if approval.get("plan_hash") != compute_plan_hash(plan): issues.append(_issue("approval_plan_hash_mismatch","approval plan_hash mismatch"))
    if approval.get("expires_at_utc") and (now_utc or utc_now()) > approval["expires_at_utc"]: issues.append(_issue("approval_expired","approval expired"))
    return {"valid": not issues, "issues": issues}
