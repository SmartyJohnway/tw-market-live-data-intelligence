from __future__ import annotations
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any
from scripts.m8r_filesystem_safety import classify_artifact_relative_path

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

def _norm_source_family(v):
    return v.strip().upper() if isinstance(v, str) else v

def _norm_context_type(v):
    return v.strip().lower() if isinstance(v, str) else v

def _norm_session(v):
    if not isinstance(v, str) or not v.strip():
        return "regular"
    value = v.strip().lower()
    return "regular" if value == "regular_session" else value

def _norm_expiry(v):
    return v.strip().upper() if isinstance(v, str) else v

def _norm_contract_selector(v):
    return v.strip().lower() if isinstance(v, str) else v

def _norm_strike(v):
    if v is None:
        return None
    raw = str(v).strip()
    try:
        dec = Decimal(raw)
    except (InvalidOperation, ValueError):
        return raw
    return format(dec.normalize(), "f")

def _norm_call_put(v):
    return v.strip().upper() if isinstance(v, str) else v

def _norm_contract_type(v):
    return v.strip().lower() if isinstance(v, str) else v

def validate_output_scope(output_policy: dict[str, Any] | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy = output_policy or {}
    root = policy.get("artifact_root", "research/m8r/planned")
    issues=[]
    if not isinstance(root,str) or not root or len(root)>MAX_OUTPUT_RELATIVE_PATH_LENGTH:
        issues.append(_issue("unsafe_output_scope","artifact_root must be a bounded relative path", field="output_policy.artifact_root"))
        root="research/m8r/planned"
    
    cls = classify_artifact_relative_path(root)
    if not cls.safe_relative or cls.rejection_code:
        issues.append(_issue("unsafe_output_scope", f"artifact_root is unsafe: {cls.rejection_code or 'unsafe_path'}", field="output_policy.artifact_root"))
    else:
        parts = set(cls.segments)
        if any(part in {".env", "secrets", "credentials"} for part in parts) or cls.normalized_relative.startswith(("frontend/public", "research/generated")):
            issues.append(_issue("unsafe_output_scope", "artifact_root must not be absolute, traversal, public, generated, or secret-bearing", field="output_policy.artifact_root"))
            
    norm_path = cls.normalized_relative if (cls.safe_relative and not cls.rejection_code) else "research/m8r/planned"
    return {"artifact_root": norm_path, "write_artifacts": False, "raw_payload_retention": False}, issues

def _target_contexts(target, request_contexts):
    return tuple(sorted(_norm_context_type(c) for c in (target.get("requested_context_types") or request_contexts or DEFAULT_CONTEXT_TYPES)))

def _requested_sources_for_target(target, request_sources, source_registry):
    explicit = "requested_source_families" in target
    requested = target.get("requested_source_families") if explicit else request_sources
    if requested is None or requested == []:
        requested = accepted_source_families(source_registry)
    return tuple(sorted(_norm_source_family(s) for s in requested)), explicit

def _local_context_mapping(target_id: str, context_type: str) -> dict[str, Any] | None:
    if context_type == "source_health":
        return {"target_id": target_id, "context_type": context_type, "source_family": None, "operation_class": "local_source_health_read", "route": "local_source_health", "network_required": False}
    if context_type == "market_session_state":
        return {"target_id": target_id, "context_type": context_type, "source_family": None, "operation_class": "local_market_clock_evaluation", "route": "local_market_clock", "network_required": False}
    return None

def _is_plan_object(value: dict[str, Any]) -> bool:
    return isinstance(value, dict) and value.get("schema_version") == PLAN_SCHEMA_VERSION and "plan_hash" in value and "targets" in value

def _is_hash_scope_object(value: dict[str, Any]) -> bool:
    return isinstance(value, dict) and value.get("schema_version") == PLAN_SCHEMA_VERSION and "targets" in value and "network_scope" in value and "plan_hash" not in value

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
    if typ == "future":
        if target.get("contract_selector"):
            issues.append(_issue("unsupported_product_scope","future contract_selector is not supported in M8R-01F; use exact expiry and monthly contract_type","target",raw_id,"contract_selector"))
        missing=[k for k in ("expiry","contract_type") if not target.get(k)]
        if missing:
            issues.append(_issue("ambiguous_identity","future identity requires exact expiry and contract_type=monthly; implicit front-month selection is not allowed","target",raw_id))
        elif _norm_contract_type(target.get("contract_type")) != "monthly":
            issues.append(_issue("unsupported_product_scope","only monthly TAIFEX futures are supported in M8R-01F","target",raw_id,"contract_type"))
    if typ == "option":
        required=("underlying","expiry","strike","call_put","contract_type")
        missing=[k for k in required if not target.get(k)]
        if missing: issues.append(_issue("ambiguous_identity","option identity requires underlying, expiry, strike, call_put, contract_type","target",raw_id))
        if _norm_contract_type(target.get("contract_type"))=="weekly" and target.get("resolution_mode") != "conversational_current": issues.append(_issue("unsupported_product_scope","weekly option runtime remains deferred for exact mode","target",raw_id))
    session = _norm_session(target.get("session", "regular"))
    if market == "TAIFEX" and session != "regular": issues.append(_issue("unsupported_session_scope","TAIFEX after-hours runtime is not accepted","target",raw_id))
    allowed_by_context, routes = _allowed_for_identity(market, typ, target)
    contexts=_target_contexts(target, request_context_types)
    sources, explicit_target_sources=_requested_sources_for_target(target, request_source_families, source_registry)
    source_policies=_source_map(source_registry)
    eligible=set(accepted_source_families(source_registry))
    for c in contexts:
        if c not in CONTEXT_TYPES: issues.append(_issue("unsupported_context_type",f"unsupported context type {c}","target",raw_id))
    for s in sources:
        pol=source_policies.get(s)
        if s not in source_policies: issues.append(_issue("unsupported_source_family",f"unsupported source family {s}","target",raw_id))
        elif pol.get("credential_required") is True: issues.append(_issue("credential_gated_source_forbidden",f"credential-gated source forbidden {s}","target",raw_id))
        elif s not in eligible: issues.append(_issue("source_not_runtime_eligible",f"source is not M8R runtime/AI eligible {s}","target",raw_id))
    if explicit_target_sources:
        incompatible = sorted(set(sources) - set(allowed_by_context.values()))
        if incompatible:
            issues.append(_issue("source_target_incompatible",f"target-level source selection includes incompatible sources: {','.join(incompatible)}","target",raw_id))
    effective_sources = tuple(sorted(set(sources) & set(allowed_by_context.values())))
    mappings=[]
    target_id=f"{market}:{typ}:{symbol}"
    derivative_identity={}
    if typ=="future":
        derivative_identity={
            "expiry": _norm_expiry(target.get("expiry")),
            "contract_type": _norm_contract_type(target.get("contract_type")),
            "session": session,
        }
        target_id += f":{derivative_identity['expiry']}:{derivative_identity['contract_type']}"
    if typ=="option":
        derivative_identity={
            "underlying": _norm_symbol(target.get("underlying")),
            "expiry": _norm_expiry(target.get("expiry")),
            "strike": _norm_strike(target.get("strike")),
            "call_put": _norm_call_put(target.get("call_put")),
            "contract_type": _norm_contract_type(target.get("contract_type")),
            "session": session,
        }
        target_id += f":{derivative_identity['underlying']}:{derivative_identity['expiry']}:{derivative_identity['strike']}:{derivative_identity['call_put']}:{derivative_identity['contract_type']}"
    duplicate_identity_key = target_id
    if typ == "option":
        duplicate_identity_key = target_id if target.get("resolution_mode") == "conversational_current" else f"{market}:{typ}:{symbol}:{derivative_identity.get('underlying')}"
    elif typ == "future":
        duplicate_identity_key = f"{market}:{typ}:{symbol}"
    for c in contexts:
        local_mapping = _local_context_mapping(target_id, c)
        if local_mapping is not None:
            mappings.append(local_mapping); continue
        required=allowed_by_context.get(c)
        if not required:
            issues.append(_issue("unsupported_context_type",f"context {c} unsupported for target identity","target",raw_id)); continue
        if required not in effective_sources:
            issues.append(_issue("source_target_incompatible",f"required source {required} not selected for {c}","target",raw_id)); continue
        route=routes[required].replace("{symbol}",symbol.lower() if required=="TWSE_MIS" else symbol)
        mappings.append({"target_id": target_id, "context_type":c,"source_family":required,"operation_class":"planned_network_fetch","route":route,"network_required": True})
    return {"input_identity":target,"target_id":target_id,"duplicate_identity_key":duplicate_identity_key,"symbol":symbol,"market":market,"instrument_type":typ,"derivative_identity":derivative_identity,"session":session if market == "TAIFEX" else None,"identity_resolution_status":"rejected" if issues else "resolved","requested_context_types":list(contexts),"requested_source_families":list(effective_sources),"requested_source_selection_mode":"target_exact" if explicit_target_sources else "request_allowlist","allowed_source_families":sorted(set(allowed_by_context.values())),"runtime_routes":routes,"planned_mappings":sorted(mappings, key=lambda x:(x.get("target_id") or "", x["context_type"], x.get("source_family") or "", x["operation_class"])),"issues":issues}

def normalize_market_context_request(request: dict[str, Any], *, source_registry=None) -> dict[str, Any]:
    issues=[]
    if not isinstance(request,dict): raise M8RValidationError([_issue("missing_required_field","request must be object")])
    if request.get("schema_version") != REQUEST_SCHEMA_VERSION: issues.append(_issue("invalid_schema_version",f"schema_version must be {REQUEST_SCHEMA_VERSION}",field="schema_version"))
    request_id=str(request.get("request_id") or "m8r-request").strip()
    if not request_id or len(request_id)>MAX_IDENTIFIER_LENGTH: issues.append(_issue("identifier_too_long","request_id is missing or too long",field="request_id"))
    targets=request.get("targets")
    if not isinstance(targets,list) or not targets: issues.append(_issue("missing_required_field","targets must be non-empty",field="targets")); targets=[]
    if len(targets)>MAX_TARGETS: issues.append(_issue("target_limit_exceeded","too many targets",field="targets"))
    req_contexts=tuple(sorted(_norm_context_type(c) for c in (request.get("requested_context_types") or DEFAULT_CONTEXT_TYPES)))
    req_sources=tuple(sorted(_norm_source_family(s) for s in (request.get("requested_source_families") or accepted_source_families(source_registry))))
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
        duplicate_key = r.get("duplicate_identity_key") or r.get("target_id")
        if duplicate_key in seen:
            if build_target_semantic_scope(seen[duplicate_key]) != build_target_semantic_scope(r):
                r["issues"].append(_issue("duplicate_target_conflict","duplicate target has conflicting definition","target",r["target_id"]))
                r["identity_resolution_status"]="rejected"
            else:
                continue
        seen[duplicate_key]=r
        (final if r["identity_resolution_status"]=="resolved" else rejected).append(r)
    if sum(len(r.get("requested_context_types",[])) for r in final+rejected)>MAX_TOTAL_TARGET_CONTEXTS: raise M8RValidationError([_issue("context_limit_exceeded","too many target-context combinations")])
    return {"schema_version":NORMALIZED_SCHEMA_VERSION,"request_id":request_id,"requested_context_types":list(req_contexts),"requested_source_families":list(req_sources),"execution_policy":{"one_shot":True,"network_execution_in_m8r01":False,"approval_required":True,"auto_retry":False},"output_policy":output_policy,"targets":final,"rejected_targets":rejected,"normalization_warnings":[],"non_goal_flags":dict(sorted(NON_GOAL_FLAGS.items()))}

def validate_market_context_request(request: dict[str, Any], *, source_registry=None) -> dict[str, Any]:
    try:
        n=normalize_market_context_request(request, source_registry=source_registry)
        return {"valid": bool(n["targets"]), "issues": [] if n["targets"] else [_issue("unresolved_identity","at least one resolved target is required")], "normalized_request": n}
    except M8RValidationError as e:
        return {"valid": False, "issues": e.issues, "normalized_request": None}

def build_target_semantic_scope(normalized_target: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_id": normalized_target.get("target_id"),
        "duplicate_identity_key": normalized_target.get("duplicate_identity_key"),
        "market": normalized_target.get("market"),
        "symbol": normalized_target.get("symbol"),
        "instrument_type": normalized_target.get("instrument_type"),
        "derivative_identity": normalized_target.get("derivative_identity") or {},
        "session": normalized_target.get("session"),
        "requested_context_types": sorted(normalized_target.get("requested_context_types", [])),
        "requested_source_families": sorted(normalized_target.get("requested_source_families", [])),
        "requested_source_selection_mode": normalized_target.get("requested_source_selection_mode"),
        "planned_mappings": sorted(normalized_target.get("planned_mappings", []), key=lambda x:(x.get("target_id") or "", x.get("context_type") or "", x.get("source_family") or "", x.get("operation_class") or "")),
    }

def build_normalized_request_hash_scope(normalized_request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(normalized_request, dict) or normalized_request.get("schema_version") != NORMALIZED_SCHEMA_VERSION:
        raise M8RValidationError([_issue("invalid_schema_version", "normalized request object required")])
    return {
        "schema_version": normalized_request.get("schema_version"),
        "execution_policy": normalized_request.get("execution_policy", {}),
        "output_policy": normalized_request.get("output_policy", {}),
        "targets": sorted((build_target_semantic_scope(t) for t in normalized_request.get("targets", [])), key=lambda x: canonical_json(x)),
        "non_goal_flags": normalized_request.get("non_goal_flags", {}),
    }

def build_plan_hash_scope(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict) or not _is_plan_object(plan):
        raise M8RValidationError([_issue("invalid_plan", "complete plan object required for plan hash computation")])
    return {
        "schema_version": plan.get("schema_version"),
        "normalized_request_hash": plan.get("normalized_request_hash"),
        "targets": [
            build_target_semantic_scope(t)
            for t in plan.get("targets", [])
        ],
        "planned_source_families": plan.get("planned_source_families", []),
        "source_to_target_context_mapping": plan.get("source_to_target_context_mapping", []),
        "network_scope": plan.get("network_scope", {}),
        "retained_scope": plan.get("bounded_retained_scope", {}),
        "output_scope": plan.get("output_scope", {}),
        "approval_required": plan.get("approval_required"),
        "non_goal_flags": plan.get("non_goal_flags", {}),
    }

def validate_plan_internal_consistency(plan: dict[str, Any]) -> dict[str, Any]:
    issues=[]
    try:
        rebuilt = build_plan_hash_scope(plan)
    except M8RValidationError as exc:
        return {"valid": False, "issues": exc.issues, "rebuilt_hash": None}
    rebuilt_hash = sha256_json(rebuilt)
    if plan.get("plan_hash") != rebuilt_hash:
        issues.append(_issue("plan_hash_mismatch", "plan.plan_hash does not match rebuilt plan scope"))
    if "hash_scope" in plan and plan.get("hash_scope") != rebuilt:
        issues.append(_issue("plan_internal_scope_mismatch", "embedded hash_scope does not match rebuilt plan scope"))
    return {"valid": not issues, "issues": issues, "rebuilt_hash": rebuilt_hash, "rebuilt_scope": rebuilt}

def compute_scope_hash(scope: dict[str, Any]) -> str:
    if not _is_hash_scope_object(scope):
        raise M8RValidationError([_issue("invalid_plan_hash_scope", "explicit hash scope object is required")])
    return sha256_json(scope)

def compute_plan_hash(plan: dict[str, Any]) -> str:
    return sha256_json(build_plan_hash_scope(plan))

def compile_market_context_execution_plan(request_or_normalized: dict[str, Any], *, source_registry=None, created_at_utc: str | None = None) -> dict[str, Any]:
    n = request_or_normalized if request_or_normalized.get("schema_version")==NORMALIZED_SCHEMA_VERSION else normalize_market_context_request(request_or_normalized, source_registry=source_registry)
    if not n["targets"]: raise M8RValidationError([_issue("unresolved_identity","at least one resolved target is required")])
    source_to_target=[]
    for t in n["targets"]:
        for m in t["planned_mappings"]: source_to_target.append(dict(m))
    source_to_target = sorted(source_to_target, key=lambda x:(x.get("target_id") or "", x["context_type"], x.get("source_family") or "", x["operation_class"]))
    operation_classes=sorted({m["operation_class"] for m in source_to_target})
    network_required=any(bool(m.get("network_required")) for m in source_to_target)
    planned_source_families=sorted({m["source_family"] for m in source_to_target if m.get("source_family")})
    plan={"schema_version":PLAN_SCHEMA_VERSION,"plan_id":None,"plan_hash":None,"normalized_request_hash":sha256_json(build_normalized_request_hash_scope(n)),"request_id":n["request_id"],"created_at_utc":created_at_utc or utc_now(),"targets":n["targets"],"rejected_targets":n["rejected_targets"],"requested_context_types":n["requested_context_types"],"planned_source_families":planned_source_families,"source_to_target_context_mapping":source_to_target,"network_required":network_required,"network_scope":{"network_required":network_required,"operation_classes":operation_classes,"network_execution_in_m8r01":False},"approval_required":True,"bounded_retained_scope":{"bounded_targets_only":True,"full_market_retained_output":False,"raw_payload_retention":False},"output_scope":n["output_policy"],"non_goal_flags":n["non_goal_flags"]}
    h=compute_plan_hash(plan)
    plan["plan_hash"]=h
    plan["plan_id"]="m8r-plan-"+h[:16]
    plan["hash_scope"]=build_plan_hash_scope(plan)
    return plan

def _parse_utc_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise M8RValidationError([_issue("invalid_approval_timestamp", "timestamp must be RFC3339 UTC string")])
    try:
        if value.endswith("Z"):
            dt = datetime.fromisoformat(value[:-1] + "+00:00")
        else:
            dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise M8RValidationError([_issue("invalid_approval_timestamp", "timestamp must be valid RFC3339 UTC")]) from exc
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise M8RValidationError([_issue("invalid_approval_timestamp", "timestamp must be timezone-aware UTC")])
    return dt

def build_approval_artifact(plan: dict[str, Any], *, approval_status="approved", approved_by="operator", approved_at_utc: str | None = None, expires_at_utc: str | None = None, single_use=True) -> dict[str, Any]:
    h=compute_plan_hash(plan)
    return {"schema_version":APPROVAL_SCHEMA_VERSION,"approval_id":"m8r-approval-"+sha256_json({"plan_id":plan["plan_id"],"plan_hash":h,"approved_by":approved_by})[:16],"plan_id":plan["plan_id"],"plan_hash":h,"approval_status":approval_status,"approved_at_utc":approved_at_utc or utc_now(),"approved_by":approved_by,"single_use":bool(single_use),"expires_at_utc":expires_at_utc,"approved_scope":{"target_ids":[t["target_id"] for t in plan["targets"]],"source_families":plan["planned_source_families"],"context_types":plan["requested_context_types"],"output_scope":plan["output_scope"]}}

def validate_approval_for_plan(approval: dict[str, Any], plan: dict[str, Any], *, now_utc: str | None = None) -> dict[str, Any]:
    issues=[]
    consistency = validate_plan_internal_consistency(plan)
    issues.extend(consistency.get("issues", []))
    rebuilt_hash = consistency.get("rebuilt_hash")
    if approval.get("schema_version") != APPROVAL_SCHEMA_VERSION: issues.append(_issue("invalid_schema_version","approval schema mismatch"))
    if approval.get("approval_status") != "approved": issues.append(_issue("approval_not_approved","approval status is not approved"))
    if approval.get("plan_id") != plan.get("plan_id"): issues.append(_issue("approval_plan_mismatch","approval plan_id mismatch"))
    if approval.get("plan_hash") != rebuilt_hash: issues.append(_issue("approval_plan_hash_mismatch","approval plan_hash mismatch"))
    try:
        _parse_utc_timestamp(approval.get("approved_at_utc"))
        expires = _parse_utc_timestamp(approval.get("expires_at_utc"))
        now = _parse_utc_timestamp(now_utc) if now_utc is not None else datetime.now(timezone.utc)
        if expires is not None and now >= expires:
            issues.append(_issue("approval_expired","approval expired"))
    except M8RValidationError as exc:
        issues.extend(exc.issues)
    return {"valid": not issues, "issues": issues}
