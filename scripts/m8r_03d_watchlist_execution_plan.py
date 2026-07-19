from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from typing import Any
from scripts.m8r_03c_conversation_contract_validator import validate_watchlist_snapshot_request, validate_watchlist_performance_request, assert_no_forbidden_keys
from scripts.m8a_official_eod_instrument_classifier import build_security_master_lookup, normalize_market as _sm_market, normalize_instrument_type
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot, build_verified_security_master_lookup, load_verified_security_master_snapshot, validate_verified_security_master_snapshot, resolve_verified_security_identity, VerifiedSecurityMasterSnapshotError

AUTH_SCHEMA_VERSION='m8r_03d_watchlist_execution_authorization.v1'
PLAN_SCHEMA_VERSION='m8r_03d_watchlist_execution_plan.v1'
MAX_WATCHLIST_TARGETS=10
ALLOWED_SOURCE_FAMILIES={'TWSE_MIS','TWSE_OPENAPI','TPEX_OPENAPI'}
AUTH_ALLOWED_FIELDS={'schema_version','authorization_id','issued_at_utc','expires_at_utc','authorized_request_hash','authorized_bundle_types','authorized_source_families','authorized_target_ids','max_target_count','network_execution_allowed','one_shot_only','one_shot_nonce','polling_allowed','scheduler_allowed','persistent_storage_allowed','raw_payload_retention_allowed','operator_approval'}
BUNDLE_TYPES={'snapshot','performance'}
BLOCKING_PLAN_CODES={'target_limit_exceeded','market_mismatch','unsupported_instrument','invalid_request','authorization_planning_inconsistency'}

def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def canonical_json(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v): return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def canonical_request_hash(request:dict)->str: return sha256_json(request)
def _parse_utc(s):
    if not isinstance(s,str): raise ValueError('invalid_utc_timestamp')
    d=datetime.fromisoformat(s[:-1]+'+00:00' if s.endswith('Z') else s)
    if d.tzinfo is None or d.utcoffset()!=timezone.utc.utcoffset(d): raise ValueError('invalid_utc_timestamp')
    return d

def _issue(code, **extra):
    return {'code': code, **extra}

def _non_empty_unique_str_list(value, field, allowed=None):
    if not isinstance(value, list) or not value:
        return None, [_issue('authorization_field_invalid', field=field)]
    if not all(isinstance(x, str) and x.strip() for x in value):
        return None, [_issue('authorization_field_invalid', field=field)]
    if len(value) != len(set(value)):
        return None, [_issue('authorization_duplicate_value', field=field)]
    if allowed is not None and not set(value).issubset(allowed):
        return None, [_issue('authorization_enum_invalid', field=field)]
    return value, []

def validate_authorization(auth:dict, *, request:dict, plan:dict, bundle_type:str, now_utc:str|None=None, require_network:bool=True)->dict:
    issues=[]; h=canonical_request_hash(request); fams={g['source_family'] for g in plan.get('source_call_groups',[]) if g.get('source_family')}
    try: assert_no_forbidden_keys(auth)
    except Exception as exc: issues.append(_issue('authorization_forbidden_key', detail=str(exc)[:120]))
    if not isinstance(auth,dict):
        return {'valid':False,'issues':[_issue('invalid_authorization_schema')],'request_hash':h,'authorized_source_families':[]}
    unknown=sorted(set(auth)-AUTH_ALLOWED_FIELDS)
    if unknown: issues.append(_issue('authorization_unknown_field', field=unknown[0]))
    if auth.get('schema_version')!=AUTH_SCHEMA_VERSION: issues.append(_issue('invalid_authorization_schema'))
    for field in ('authorization_id','one_shot_nonce'):
        if not isinstance(auth.get(field),str) or not auth.get(field).strip(): issues.append(_issue('authorization_field_invalid', field=field))
    if not isinstance(auth.get('authorized_request_hash'),str) or not re.fullmatch(r'[0-9a-f]{64}', auth.get('authorized_request_hash') or ''): issues.append(_issue('authorization_field_invalid', field='authorized_request_hash'))
    elif auth.get('authorized_request_hash')!=h: issues.append(_issue('request_hash_mismatch'))
    bundles, e = _non_empty_unique_str_list(auth.get('authorized_bundle_types'), 'authorized_bundle_types', BUNDLE_TYPES); issues.extend(e)
    sources, e = _non_empty_unique_str_list(auth.get('authorized_source_families'), 'authorized_source_families', ALLOWED_SOURCE_FAMILIES); issues.extend(e)
    targets_allowed, e = _non_empty_unique_str_list(auth.get('authorized_target_ids'), 'authorized_target_ids'); issues.extend(e)
    if bundles and bundle_type not in set(bundles): issues.append(_issue('unauthorized_bundle_type'))
    targets=plan.get('target_order') or []
    if targets_allowed and not set(targets).issubset(set(targets_allowed)): issues.append(_issue('unauthorized_target'))
    if not isinstance(auth.get('max_target_count'), int) or auth.get('max_target_count') <= 0: issues.append(_issue('authorization_field_invalid', field='max_target_count'))
    elif len(targets)>auth.get('max_target_count'): issues.append(_issue('target_limit_exceeded'))
    if sources and not fams.issubset(set(sources)): issues.append(_issue('unauthorized_source_family'))
    for k,want in {'network_execution_allowed':True,'one_shot_only':True,'polling_allowed':False,'scheduler_allowed':False,'persistent_storage_allowed':False,'raw_payload_retention_allowed':False}.items():
        if auth.get(k) is not want: issues.append(_issue('authorization_flag_rejected', field=k))
    if not isinstance(auth.get('operator_approval'), dict): issues.append(_issue('authorization_field_invalid', field='operator_approval'))
    else:
        try: assert_no_forbidden_keys(auth.get('operator_approval'))
        except Exception as exc: issues.append(_issue('authorization_forbidden_key', field='operator_approval', detail=str(exc)[:120]))
    try:
        issued=_parse_utc(auth.get('issued_at_utc')); expires=_parse_utc(auth.get('expires_at_utc'))
        now=_parse_utc(now_utc) if now_utc else datetime.now(timezone.utc)
        if expires <= issued: issues.append(_issue('authorization_expiry_invalid'))
        if now>=expires: issues.append(_issue('authorization_expired'))
    except Exception: issues.append(_issue('authorization_timestamp_invalid'))
    if require_network and auth.get('network_execution_allowed') is not True: issues.append(_issue('network_not_authorized'))
    if any(i.get('blocking') for i in plan.get('issues', [])): issues.append(_issue('authorization_planning_inconsistency'))
    return {'valid':not issues,'issues':issues,'request_hash':h,'authorized_source_families':sorted(auth.get('authorized_source_families') or [])}

def _market_to_canonical(prefix):
    return {'TWSE':'listed','TPEX':'tpex_otc'}.get(prefix)
def _canonical_to_prefix(canonical):
    return {'listed':'TWSE','tpex_otc':'TPEX'}.get(canonical)
def _lookup_entry(lookup, canonical_market, code):
    return lookup.get((canonical_market, code)) or lookup.get(f'{canonical_market}:{code}') or lookup.get(code)
def _resolve_verified_security(tid: str, snapshot_lookup, *, allow_fixture_snapshot: bool=False) -> dict:
    parts=tid.split(':'); requested={'target_id':tid}
    market_context=parts[0] if len(parts)==2 else None
    rr=resolve_verified_security_identity(tid, snapshot_lookup, market_context=market_context, allow_fixture_snapshot=allow_fixture_snapshot, execute_mode=True)
    sel=rr.get('selected') or {}
    if rr.get('resolution_status')!='resolved':
        code = {'ambiguous':'identity_conflict','quarantined':'lifecycle_unsupported' if 'fixture_observation_only_rejected' in rr.get('reason_codes',[]) else 'identity_conflict','not_found':'identity_unresolved'}.get(rr.get('resolution_status'),'identity_unresolved')
        return {'target_id':tid,'security_code':parts[1] if len(parts)==2 else None,'security_name':None,'canonical_market':_market_to_canonical(market_context),'instrument_type':None,'listing_status':None,'lifecycle_state':'unresolved','lifecycle_resolution_status':'unavailable','resolution_status':code,'resolution_evidence':[{'source':'verified_security_master_snapshot','resolution':rr}],'requested_identity':requested}
    ident=sel.get('identity') or {}; cls=sel.get('classification') or {}; life=sel.get('lifecycle') or {}; elig=sel.get('execution_eligibility') or {}
    canonical=_market_to_canonical(cls.get('market')); typ=cls.get('instrument_type')
    status='resolved'; caveats=list(sel.get('caveats') or [])
    if canonical != _market_to_canonical(market_context): status='market_mismatch'
    elif elig.get('status')=='blocked': status='lifecycle_unsupported' if 'lifecycle_blocks_current_execution' in elig.get('reason_codes',[]) or 'fixture_observation_only' in elig.get('reason_codes',[]) else 'unsupported_instrument' if 'unsupported_instrument_type' in elig.get('reason_codes',[]) else 'identity_conflict'
    elif elig.get('status')=='allowed_with_caveat': caveats += elig.get('reason_codes',[])
    execution_policy='execution_allowed' if elig.get('status')=='allowed' else 'execution_allowed_with_caveat' if elig.get('status')=='allowed_with_caveat' else 'execution_blocked'
    return {'target_id':tid,'security_code':ident.get('security_code'),'security_name':ident.get('security_name_zh') or ident.get('security_name_en'),'canonical_market':canonical,'instrument_type':typ,'listing_status':life.get('state'),'lifecycle_state':life.get('state'),'lifecycle_resolution_status':life.get('resolution_status'),'execution_policy':execution_policy,'resolution_caveats':caveats,'resolution_status':status,'snapshot_id':sel.get('snapshot_id'),'record_id':sel.get('record_id'),'record_hash':sel.get('record_hash'),'classification_status':cls.get('classification_status'),'classification_execution_policy':sel.get('classification_execution_policy'),'execution_eligibility':elig,'resolution_evidence':[{'source':'verified_security_master_snapshot','snapshot_id':sel.get('snapshot_id'),'record_id':sel.get('record_id'),'record_hash':sel.get('record_hash'),'resolution_reason':sel.get('resolution_reason')}], 'requested_identity':requested}

def _resolve_security(tid: str, security_master=None, *, allow_fixture_snapshot: bool=False) -> dict:
    if isinstance(security_master, ValidatedVerifiedSecurityMasterSnapshot):
        validate_verified_security_master_snapshot(security_master.snapshot, security_master.manifest, allow_fixture_snapshot=allow_fixture_snapshot)
        return _resolve_verified_security(tid, build_verified_security_master_lookup(security_master.snapshot), allow_fixture_snapshot=allow_fixture_snapshot)
    if isinstance(security_master, dict) and (security_master.get('schema_version')=='tw_verified_security_master_snapshot.v1' or (security_master.get('snapshot') and security_master.get('by_canonical') is not None)):
        raise VerifiedSecurityMasterSnapshotError('unvalidated_verified_snapshot_injection_rejected')
    parts=tid.split(':'); requested={'target_id':tid}; evidence=[]
    if len(parts)!=2 or parts[0] not in {'TWSE','TPEX'} or not re.fullmatch(r'[A-Z0-9._-]{1,20}',parts[1]):
        return {'target_id':tid,'security_code':None,'security_name':None,'canonical_market':None,'instrument_type':None,'listing_status':None,'lifecycle_state':'unresolved','resolution_status':'identity_unresolved','resolution_evidence':[{'code':'invalid_target_id'}],'requested_identity':requested}
    prefix, code=parts; requested_market=_market_to_canonical(prefix)
    lookup=security_master if security_master is not None else build_security_master_lookup()
    found=[]
    for market in ('listed','tpex_otc'):
        entry=_lookup_entry(lookup, market, code) if isinstance(lookup, dict) else None
        if isinstance(entry, str): entry={'instrument_type':entry}
        if isinstance(entry, dict): found.append((market, entry))
    if not found:
        return {'target_id':tid,'security_code':code,'security_name':None,'canonical_market':None,'instrument_type':None,'listing_status':None,'lifecycle_state':'unknown','lifecycle_resolution_status':'unavailable','resolution_status':'identity_unresolved','resolution_evidence':[{'code':'security_master_miss','requested_market':requested_market}],'requested_identity':requested}
    exact=[(m,e) for m,e in found if m==requested_market]
    if not exact:
        canonical_market, entry = found[0]
    elif len(found)>1 and not exact[0][1].get('cross_market_duplicate_policy') == 'exact_requested_market_ok':
        return {'target_id':tid,'security_code':code,'security_name':None,'canonical_market':requested_market,'instrument_type':None,'listing_status':None,'lifecycle_state':'unknown','lifecycle_resolution_status':'unavailable','resolution_status':'identity_conflict','resolution_evidence':[{'code':'cross_market_duplicate','markets':[m for m,_ in found]}],'requested_identity':requested}
    else:
        canonical_market, entry = exact[0]
    typ=normalize_instrument_type(entry.get('instrument_type')) or entry.get('instrument_type')
    lifecycle_supplied='lifecycle_state' in entry or 'listing_status' in entry
    lifecycle=entry.get('lifecycle_state') or entry.get('listing_status') if lifecycle_supplied else 'unknown'
    listing=entry.get('listing_status')
    lifecycle_status='resolved' if lifecycle_supplied else 'unavailable'
    execution_policy='execution_allowed'
    caveats=[]
    status='resolved'
    if canonical_market != requested_market: status='market_mismatch'
    elif typ not in {'equity','etf'}: status='unsupported_instrument'
    elif lifecycle_supplied and lifecycle not in {'active','listed','trading'}: status='lifecycle_unsupported'
    elif not lifecycle_supplied:
        execution_policy='execution_allowed_with_caveat'; caveats.append('lifecycle_evidence_unavailable_not_assumed_active')
    return {'target_id':tid,'security_code':code,'security_name':entry.get('security_name') or entry.get('name'),'canonical_market':canonical_market,'instrument_type':typ,'listing_status':listing,'lifecycle_state':lifecycle,'lifecycle_resolution_status':lifecycle_status,'execution_policy':execution_policy,'resolution_caveats':caveats,'resolution_status':status,'resolution_evidence':[{'source':entry.get('source'),'provenance':entry.get('provenance'),'coverage_mode':entry.get('coverage_mode')}], 'requested_identity':requested}

def _target_from_resolution(res: dict) -> dict:
    status=res['resolution_status']; canonical=res.get('canonical_market'); prefix=_canonical_to_prefix(canonical) if canonical else None
    issues=[]
    if status!='resolved': issues.append(_issue(status, blocking=status in {'market_mismatch','unsupported_instrument','lifecycle_unsupported','identity_conflict'}, target_id=res['target_id']))
    for caveat in res.get('resolution_caveats') or []: issues.append(_issue(caveat, blocking=False, target_id=res['target_id']))
    resolved={'target_id':res['target_id'],'symbol':res.get('security_code'),'market':prefix,'canonical_market':canonical,'instrument_type':res.get('instrument_type'),'security_name':res.get('security_name'),'listing_status':res.get('listing_status'),'lifecycle_state':res.get('lifecycle_state'),'lifecycle_resolution_status':res.get('lifecycle_resolution_status'),'execution_policy':res.get('execution_policy'),'resolution_caveats':res.get('resolution_caveats') or [],'snapshot_id':res.get('snapshot_id'),'record_id':res.get('record_id'),'record_hash':res.get('record_hash'),'classification_status':res.get('classification_status'),'execution_eligibility':res.get('execution_eligibility')} if status=='resolved' else {}
    return {'target_id':res['target_id'],'requested_identity':res.get('requested_identity') or {'target_id':res['target_id']},'resolved_identity':resolved,'identity_status':'resolved' if status=='resolved' else status,'market':prefix,'canonical_market':canonical,'instrument_type':res.get('instrument_type'),'security_code':res.get('security_code'),'security_name':res.get('security_name'),'listing_status':res.get('listing_status'),'lifecycle_state':res.get('lifecycle_state'),'lifecycle_resolution_status':res.get('lifecycle_resolution_status'),'execution_policy':res.get('execution_policy'),'resolution_caveats':res.get('resolution_caveats') or [],'resolution_status':status,'snapshot_id':res.get('snapshot_id'),'record_id':res.get('record_id'),'record_hash':res.get('record_hash'),'classification_status':res.get('classification_status'),'classification_execution_policy':res.get('classification_execution_policy'),'execution_eligibility':res.get('execution_eligibility'),'resolution_evidence':res.get('resolution_evidence') or [],'blocking_issues':issues}

def build_execution_plan(request:dict, *, bundle_type:str, generated_at_utc:str|None=None, security_master=None, verified_snapshot_path:str|None=None, verified_snapshot_manifest_path:str|None=None, allow_fixture_snapshot:bool=False, source_capability_registry:dict|None=None)->dict:
    req=validate_watchlist_snapshot_request(request) if bundle_type=='snapshot' else validate_watchlist_performance_request(request)
    if verified_snapshot_path or verified_snapshot_manifest_path:
        if not (verified_snapshot_path and verified_snapshot_manifest_path): raise VerifiedSecurityMasterSnapshotError('snapshot_and_manifest_required')
        security_master=load_verified_security_master_snapshot(verified_snapshot_path, verified_snapshot_manifest_path, allow_fixture_snapshot=allow_fixture_snapshot)

    # 載入並解析 source capability registry
    if source_capability_registry is None:
        source_capability_registry = json.loads(Path("docs/data_capabilities/m8_source_capability_registry.json").read_text(encoding="utf-8"))

    # Schema 驗證
    if "schema_version" not in source_capability_registry:
        raise ValueError("invalid_capability_registry_schema: missing schema_version")
    if source_capability_registry["schema_version"] != "m8_source_capability_registry.v1":
        raise ValueError(f"invalid_capability_registry_schema: expected m8_source_capability_registry.v1, got {source_capability_registry['schema_version']}")

    # 判定是否啟用 Phase C 對話啟動模式
    phase_c_active = False
    if source_capability_registry.get("phase_c_activation_status") == "conversation_driven_enabled_with_caveats":
        if req.get("execution_policy", {}).get("execution_profile") == "phase_c_conversation_driven_one_shot.v1":
            phase_c_active = True

    # 載入 Activation Policy (作為唯一 Source of Truth)
    default_max_targets = 10
    hard_max_targets = 50
    default_max_operations = 30
    hard_max_operations = 100
    fallback_policy = "registry_governed"
    partial_success_policy = "allowed"
    artifact_retention_days = 30

    if phase_c_active:
        try:
            policy_path = Path("docs/data_capabilities/m8r_03e_phase_c_activation_policy.json")
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            required_policy_fields = {"schema_version", "activation_profile_id", "activation_state", "resource_bounds", "partial_success_policy", "fallback_policy", "artifact_retention"}
            if not required_policy_fields.issubset(policy):
                raise ValueError("missing_required_policy_fields")

            bounds = policy["resource_bounds"]
            if not all(k in bounds for k in ["default_max_targets", "hard_max_targets", "default_max_operations", "hard_max_operations"]):
                raise ValueError("invalid_resource_bounds")

            retention = policy["artifact_retention"]
            if not all(k in retention for k in ["default_retention_days", "expired_artifact_behavior"]):
                raise ValueError("invalid_retention_policy")

            default_max_targets = bounds["default_max_targets"]
            hard_max_targets = bounds["hard_max_targets"]
            default_max_operations = bounds["default_max_operations"]
            hard_max_operations = bounds["hard_max_operations"]
            fallback_policy = policy["fallback_policy"]
            partial_success_policy = policy["partial_success_policy"]
            artifact_retention_days = retention["default_retention_days"]
        except Exception as exc:
            raise RuntimeError(f"failed_to_load_activation_policy: {str(exc)}")

    # active_runtime_source_families 欄位缺失或為空列表時預設為空 set (Fail-Closed)
    act_list = source_capability_registry.get("active_runtime_source_families")
    if act_list is None:
        active_families = set()
    else:
        active_families = set(act_list)

    # 動態 sources 檢查，不再依賴硬編碼名稱
    source_activation_states = {}
    source_exec_status = {}
    for src in source_capability_registry.get("sources", []):
        f = src.get("source_family")
        if f:
            source_activation_states[f] = src.get("phase_c_activation_state")
            flag_name = f"{f.lower()}_runtime_executable"
            root_val = source_capability_registry.get(flag_name)
            inner_val = (source_capability_registry.get("m8_active_consolidated_status") or {}).get(flag_name)

            if root_val is None:
                root_val = src.get("runtime_executable") is True
            if inner_val is None:
                inner_val = True

            source_exec_status[f] = root_val is True and inner_val is True

    def is_source_activated(fam):
        if fam not in active_families:
            return False

        if not phase_c_active:
            return source_exec_status.get(fam, False)

        if source_activation_states.get(fam) != "enabled_one_shot":
            return False
        return source_exec_status.get(fam, False)

    # 實作完全 registry-driven 的動態尋找最佳來源機制 (具備向後相容 fallback)
    def find_best_source(market, timing_class):
        for src in source_capability_registry.get("sources", []):
            fam = src.get("source_family")
            if not fam: continue
            if not is_source_activated(fam): continue

            if fam == "TWSE_OPENAPI" and market.upper() != "TWSE": continue
            if fam == "TPEX_OPENAPI" and market.upper() != "TPEX": continue

            src_timing = src.get("timing_class")
            if not src_timing:
                if fam == "TWSE_MIS": src_timing = "liveish_intraday_snapshot"
                elif fam in ("TWSE_OPENAPI", "TPEX_OPENAPI"): src_timing = "official_eod"

            if src_timing != timing_class: continue

            scope = src.get("market_scope") or {}
            if not scope:
                if fam == "TWSE_MIS": scope = {"TWSE": "listed", "TPEX": "tpex_otc"}
                elif fam == "TWSE_OPENAPI": scope = {"TWSE": "listed EOD reference"}
                elif fam == "TPEX_OPENAPI": scope = {"TPEX": "tpex_otc EOD reference"}

            if any(k.upper() == market.upper() or (k.lower() == 'taiwan_equity' and market.upper() in ('TWSE', 'TPEX')) for k in scope):
                return src
        return None

    ids=list(req['persistent_watchlist_reference']['enabled_target_ids'])
    targets=[]; groups=[]; issues=[]
    for i,tid in enumerate(ids):
        r=_target_from_resolution(_resolve_security(tid, security_master, allow_fixture_snapshot=allow_fixture_snapshot)); cur={}; eod={}; expected='unavailable'
        if r['identity_status']=='resolved':
            expected='usable'; market=r['market']; code=r['security_code']

            if phase_c_active:
                # Phase C 啟用時：完全由 registry 驅動的動態匹配
                live_src = find_best_source(market, 'liveish_intraday_snapshot')
                eod_src = find_best_source(market, 'official_eod')

                if bundle_type=='snapshot' and live_src:
                    cur_fam = live_src["source_family"]
                    cur={'source_family':cur_fam,'route':('tse_' if market=='TWSE' else 'otc_')+code.lower()+'.tw','operation_class':'planned_network_fetch'}
                if eod_src:
                    eod_fam = eod_src["source_family"]
                    eod={'source_family':eod_fam,'route':eod_fam,'operation_class':'planned_network_fetch'}
            else:
                # 傳統模式：回退到 PR #157 原始硬編碼路由
                status_dict = source_capability_registry.get("m8_active_consolidated_status") or {}
                def get_flag(name):
                    root_val = source_capability_registry.get(name)
                    inner_val = status_dict.get(name)
                    if root_val is None:
                        return inner_val is True
                    return root_val is True and inner_val is True
                twse_mis_exec = get_flag("twse_mis_runtime_executable") and ("TWSE_MIS" in active_families)
                twse_openapi_exec = get_flag("twse_openapi_runtime_executable") and ("TWSE_OPENAPI" in active_families)
                tpex_openapi_exec = get_flag("tpex_openapi_runtime_executable") and ("TPEX_OPENAPI" in active_families)

                if bundle_type=='snapshot' and twse_mis_exec:
                    cur={'source_family':'TWSE_MIS','route':('tse_' if market=='TWSE' else 'otc_')+code.lower()+'.tw','operation_class':'planned_network_fetch'}
                if market=='TWSE' and twse_openapi_exec:
                    eod={'source_family':'TWSE_OPENAPI','route':'TWSE_OPENAPI','operation_class':'planned_network_fetch'}
                elif market=='TPEX' and tpex_openapi_exec:
                    eod={'source_family':'TPEX_OPENAPI','route':'TPEX_OPENAPI','operation_class':'planned_network_fetch'}

            if not cur and not eod:
                expected = 'unavailable'
            elif not cur or not eod:
                expected = 'partial'

            if cur: groups.append({'source_family':cur['source_family'],'context_type':'liveish_observation','target_ids':[tid],'network_required':True})
            if eod: groups.append({'source_family':eod['source_family'],'context_type':'official_eod_reference','target_ids':[tid],'network_required':True,'history_window':_history_window(req) if bundle_type=='performance' else {'latest_completed_eod_only':True}})
        targets.append({**r,'current_source_plan':cur,'eod_source_plan':eod,'expected_coverage':expected}); issues.extend(r.get('blocking_issues', []))

    # 限制與 Bounds 判定
    if phase_c_active:
        planned_ops = []
        for t in targets:
            tid = t['target_id']
            if t.get('current_source_plan'):
                cur_plan = t['current_source_plan']
                planned_ops.append({
                    "operation_id": f"op-{tid}-{cur_plan['source_family']}",
                    "target_id": tid,
                    "source_family": cur_plan['source_family'],
                    "operation_type": "current_snapshot",
                    "timing_class": "liveish_intraday_snapshot",
                    "fallback_allowed": True
                })
            if t.get('eod_source_plan'):
                eod_plan = t['eod_source_plan']
                planned_ops.append({
                    "operation_id": f"op-{tid}-{eod_plan['source_family']}",
                    "target_id": tid,
                    "source_family": eod_plan['source_family'],
                    "operation_type": "official_eod",
                    "timing_class": "official_eod",
                    "fallback_allowed": True
                })

        # Session-level dependency operations: declared in preview so the user
        # and operator can see that calendar and closure network calls will be
        # made after authorization. These are NOT target-level operations.
        # They use sentinel target_id '_session' to distinguish them.
        # Cache-hit path: network_call will not actually occur, but it must be
        # declared because cache miss triggers a real HTTP request.
        planned_ops.append({
            "operation_id": "op-_session-TWSE_OPENAPI-calendar",
            "target_id": "_session",
            "source_family": "TWSE_OPENAPI",
            "operation_type": "session_calendar_lookup",
            "timing_class": "request_session_context",
            "fallback_allowed": True
        })
        planned_ops.append({
            "operation_id": "op-_session-NCDR_DGPA_CLOSURE_CAP-closure",
            "target_id": "_session",
            "source_family": "NCDR_DGPA_CLOSURE_CAP",
            "operation_type": "session_closure_lookup",
            "timing_class": "request_session_context",
            "fallback_allowed": False
        })

        target_count = len(ids)
        operation_count = len(planned_ops)  # includes 2 session-level ops
        expanded_scope = (target_count > default_max_targets and target_count <= hard_max_targets) or (operation_count > default_max_operations and operation_count <= hard_max_operations)

        if target_count > hard_max_targets or operation_count > hard_max_operations:
            issues.append({'code': 'rejected_resource_bound', 'blocking': True, 'target_count': target_count, 'operation_count': operation_count})

        max_target_count = hard_max_targets
    else:
        if len(ids) > 10:
            issues.append({'code': 'target_limit_exceeded', 'max_target_count': 10, 'blocking': True})
        max_target_count = 10
        planned_ops = []
        expanded_scope = False
        target_count = len(ids)
        operation_count = 0

    # merge deterministic groups
    merged={}
    for g in groups:
        k=(g['source_family'],g['context_type'],canonical_json(g.get('history_window',{})))
        merged.setdefault(k,{**g,'target_ids':[]})['target_ids'].extend(g['target_ids'])
    groups=[{**v,'target_ids':sorted(v['target_ids'], key=ids.index)} for k,v in sorted(merged.items())]
    base={'schema_version':PLAN_SCHEMA_VERSION,'request_id':req['request_id'],'request_hash':canonical_request_hash(req),'bundle_type':bundle_type,'target_order':ids,'targets':targets,'source_call_groups':groups,'network_required':bool(groups),'authorization_required':True,'max_target_count':max_target_count,'issues':issues}
    base['plan_id']='m8r03d-plan-'+sha256_json({k:base[k] for k in ('request_id','request_hash','bundle_type','target_order','targets','source_call_groups')})[:16]
    base['created_at_utc']=generated_at_utc or utc_now()

    # 產生 preview 物件 (綁定完整 preview 屬性內容的 SHA256 雜湊)
    if phase_c_active:
        preview_body = {
            "schema_version": "m8r_phase_c_execution_preview.v1",
            "request_id": req["request_id"],
            "request_summary": req.get("original_user_text") or "取得指定台股目前市場狀況",
            "targets": ids,
            "target_count": target_count,
            "planned_sources": sorted(list(set(op["source_family"] for op in planned_ops))),
            "planned_operations": planned_ops,
            "operation_count": operation_count,
            "estimated_network_calls": operation_count,
            "expanded_scope": expanded_scope,
            "fallback_policy": fallback_policy,
            "partial_success_policy": partial_success_policy,
            "artifact_retention_days": artifact_retention_days,
            "requires_user_confirmation": True
        }
        preview_hash = sha256_json(preview_body)
        preview_id = f"preview-{preview_hash}"
        preview = {
            "preview_id": preview_id,
            **preview_body
        }
        base["execution_preview"] = preview

    return base

def _history_window(req):
    days=req['conversation_intent']['time_scope'].get('lookback_trading_days') or 20
    need={1:2,5:6,10:11,20:21}.get(days, min(21, days+1 if isinstance(days,int) else 21))
    return {'requested_lookback_trading_days':days,'minimum_valid_closes':need,'buffer_trading_days':5,'bounded':True}

def plan_has_blocking_issues(plan: dict) -> bool:
    return any(i.get('blocking') or i.get('code') in BLOCKING_PLAN_CODES for i in plan.get('issues', []))
