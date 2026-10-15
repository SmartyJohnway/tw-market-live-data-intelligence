from __future__ import annotations
import json, os
from pathlib import Path, PurePosixPath
from typing import Any
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan, validate_authorization, utc_now, sha256_json, plan_has_blocking_issues
from scripts.m8r_03d_watchlist_source_integration import normalize_twse_mis_watchlist_observation, normalize_twse_openapi_watchlist_observation, normalize_tpex_openapi_watchlist_observation
from scripts.m8r_03c_watchlist_bundle_builder import build_watchlist_snapshot_bundle, build_watchlist_performance_bundle
from scripts.m8a_twse_official_eod_adapter import execute_twse_official_eod_adapter
from scripts.m8a_tpex_official_eod_adapter import execute_tpex_official_eod_adapter
from scripts.m5k_common import execute_live_observation
from scripts.m8r_filesystem_safety import atomic_write_text, safe_destination, validate_authorized_root, classify_artifact_relative_path, FilesystemSafetyError, atomic_create_text_exclusive

RESULT_SCHEMA_VERSION='m8r_03d_watchlist_execution_result.v1'
AUTHORIZATION_CONSUMPTION_ROOT=Path('artifacts/m8r_03d_authorization_consumption')
FORBIDDEN_ARTIFACT_TOKENS=('raw_payload"','cookies','session_id','access_token','refresh_token','msgArray')
MARKET_ALIASES={'TWSE':{'TWSE','listed','twse','tse'},'TPEX':{'TPEX','tpex','tpex_otc','otc'}}

class M8R03DExecutionError(RuntimeError): pass

def _safe_root(root):
    raw = str(root).replace('\\', '/')
    parts = set(p.lower() for p in raw.split('/') if p not in ('', '.'))
    if '..' in parts or any(x in parts for x in ('.env','secrets','credentials')):
        raise ValueError('unsafe_artifact_root')
    return validate_authorized_root(root)

def _write_json(root:Path, path:Path, data:Any):
    text=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
    low=text.lower()
    if any(t.lower() in low for t in FORBIDDEN_ARTIFACT_TOKENS): raise ValueError('forbidden_artifact_content')
    atomic_write_text(root, path.relative_to(root), text+'\n')

def _load_production_calendar(evaluation_time: datetime, authorized_root: Path) -> tuple[dict | None, str]:
    """Fetch or load-from-cache the official TWSE trading calendar.

    Must only be called AFTER authorization has been claimed (anti-replay passed).
    Uses atomic_write_text so the cache is never left in a partially-written state.
    Records full provenance so the cache artifact can be audited.
    """
    relative_cache_path = Path('twse_trading_calendar.json')
    cache_path = authorized_root / relative_cache_path

    if cache_path.exists():
        try:
            from scripts.twse_trading_calendar import load_twse_trading_calendar_artifact
            loaded = load_twse_trading_calendar_artifact(cache_path)
            if loaded.get("year") == evaluation_time.year:
                return loaded, "cache_hit"
        except Exception:
            pass  # stale / corrupt cache — fall through to fetch

    import urllib.request
    from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule
    url = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) tw-market-live-data-intelligence/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            records = json.loads(response.read().decode('utf-8'))

        calendar_artifact = build_twse_trading_calendar_from_holiday_schedule(
            year=evaluation_time.year,
            holiday_schedule_records=records
        )

        # Attach provenance so the cache artifact is auditable.
        calendar_artifact["_cache_provenance"] = {
            "retrieved_at_utc": utc_now(),
            "source_url": url,
            "source_contract_id": "TWSE_OPENAPI_holidaySchedule",
            "year": evaluation_time.year,
        }

        try:
            content = json.dumps(calendar_artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            # atomic_write_text requires a path relative to authorized_root.
            atomic_write_text(authorized_root, relative_cache_path, content)
        except Exception:
            pass  # cache write failure is non-fatal

        return calendar_artifact, "network_fetch"
    except Exception:
        return None, "unresolved"


def preflight(request:dict, *, bundle_type:str, generated_at_utc:str|None=None, security_master=None, source_capability_registry=None):
    plan=build_execution_plan(request,bundle_type=bundle_type,generated_at_utc=generated_at_utc,security_master=security_master,source_capability_registry=source_capability_registry)
    return {'mode':'preflight','request_hash':plan['request_hash'],'plan':plan,'network_calls_performed':False,'observation_count':0,'status':'blocked_preflight' if plan_has_blocking_issues(plan) else 'success'}

def execute_watchlist(request:dict, *, mode:str, bundle_type:str, authorization:dict|None=None, fixture_source_data:dict|None=None, artifact_root:str='artifacts/m8r_03d', run_id:str|None=None, generated_at_utc:str|None=None, executors:dict|None=None, security_master=None, source_capability_registry=None, preview:dict|None=None, approval:dict|None=None)->dict:
    started=generated_at_utc or utc_now(); run_id=run_id or 'm8r03d-'+started.replace(':','').replace('-','')
    artifact_root_path=_safe_root(artifact_root)
    safe_destination(artifact_root_path, run_id, create_parent=False)

    # 載入並解析 source capability registry
    if source_capability_registry is None:
        try:
            source_capability_registry = json.loads(Path("docs/data_capabilities/m8_source_capability_registry.json").read_text(encoding="utf-8"))
        except Exception:
            source_capability_registry = {}

    plan=build_execution_plan(request,bundle_type=bundle_type,generated_at_utc=started,security_master=security_master,source_capability_registry=source_capability_registry)
    if mode not in {'preflight','fixture','execute'}: raise ValueError('invalid_mode')

    # 判定是否啟用 Phase C 對話啟動模式
    phase_c_active = False
    if source_capability_registry.get("phase_c_activation_status") == "conversation_driven_enabled_with_caveats":
        if request.get("execution_policy", {}).get("execution_profile") == "phase_c_conversation_driven_one_shot.v1":
            phase_c_active = True

    if mode=='preflight' or plan_has_blocking_issues(plan):
        status='blocked_preflight' if plan_has_blocking_issues(plan) else 'success'
        return _result(run_id,mode,started,utc_now(),request,plan,authorization if mode=='execute' and not phase_c_active else None,[],None,status,plan.get('issues',[]),artifact_root_path,source_execution_summary={'planned_source_call_groups':plan.get('source_call_groups',[]),'group_results':[],'network_calls_performed':False,'network_default_enabled':False,'polling':False,'scheduler':False},write=False,preview=preview,approval=approval)

    # calendar_artifact and closure_events are resolved AFTER authorization
    # (see post-claim block below). Initialize to None here so fixture mode
    # can populate them from fixture_source_data.
    calendar_artifact = None
    closure_events = None
    if mode != 'execute':
        if isinstance(fixture_source_data, dict):
            calendar_artifact = fixture_source_data.get("calendar_artifact") or fixture_source_data.get("trading_calendar_artifact")
            closure_events = fixture_source_data.get("closure_events")


    if mode=='execute':
        if phase_c_active:
            # 載入並校驗 Activation Policy (Fail-Closed)
            try:
                policy_path = Path("docs/data_capabilities/m8r_03e_phase_c_activation_policy.json")
                policy = json.loads(policy_path.read_text(encoding="utf-8"))
                required_policy_fields = {"schema_version", "activation_profile_id", "activation_state", "resource_bounds", "partial_success_policy", "fallback_policy", "artifact_retention"}
                if not required_policy_fields.issubset(policy):
                    raise ValueError("missing_required_policy_fields")
            except Exception as exc:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'policy_load_failed','detail':str(exc)[:120]}],artifact_root_path,write=False)

            # 1. 驗證 Preview
            if not preview or not isinstance(preview, dict):
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'preview_missing'}],artifact_root_path,write=False)

            # 執行完整 JSON Schema 驗證
            try:
                import jsonschema
                schema_path = Path("schemas/m8r_phase_c_execution_preview.schema.json")
                if not schema_path.exists():
                    raise FileNotFoundError("missing execution preview schema file")
                schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
                jsonschema.validate(instance=preview, schema=schema_data)
            except Exception as exc:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'invalid_preview_schema','detail':str(exc)[:120]}],artifact_root_path,write=False)

            if preview.get('request_id') != request.get('request_id'):
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'preview_request_id_mismatch'}],artifact_root_path,write=False)

            # 驗證 Request Policy 中的 network_allowed 屬性，防範靜默改寫
            if request.get("execution_policy", {}).get("network_allowed") is not True:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'network_forbidden_by_request_policy','blocking':True}],artifact_root_path,write=False)

            # 2. 驗證 Approval
            if not approval or not isinstance(approval, dict):
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'approval_missing'}],artifact_root_path,write=False)
            if approval.get('schema_version') != 'm8r_phase_c_conversation_approval.v1':
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'invalid_approval_schema'}],artifact_root_path,write=False)
            if approval.get('request_id') != request.get('request_id'):
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'approval_request_id_mismatch'}],artifact_root_path,write=False)
            if approval.get('approval_status') != 'approved':
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'approval_status_not_approved'}],artifact_root_path,write=False)

            # 3. 綁定 Planner 產生的 Canonical Preview Digest
            canonical_preview = plan.get("execution_preview")
            if not canonical_preview:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'canonical_preview_missing'}],artifact_root_path,write=False)

            # 內容雜湊重算與比對，確保 Preview 無任何欄位被惡意篡改
            caller_body = {k: v for k, v in preview.items() if k != "preview_id"}
            expected_id = "preview-" + sha256_json(caller_body)
            
            if preview.get('preview_id') != expected_id:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'preview_plan_mismatch','detail':'preview_id does not match caller content hash'}],artifact_root_path,write=False)
            if expected_id != canonical_preview['preview_id']:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'preview_plan_mismatch','detail':'caller preview content differs from canonical planner preview'}],artifact_root_path,write=False)
            if approval.get('preview_id') != canonical_preview['preview_id']:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'approval_referenced_different_preview'}],artifact_root_path,write=False)

            # 4. Preview 與實際 Plan 的一致性比對 (only target-level ops; session ops use sentinel '_session' target_id)
            actual_ops = []
            for t in plan.get('targets', []):
                tid = t['target_id']
                if t.get('current_source_plan'):
                    cur_plan = t['current_source_plan']
                    actual_ops.append({
                        "target_id": tid,
                        "source_family": cur_plan["source_family"],
                        "operation_type": "current_snapshot",
                        "timing_class": "liveish_intraday_snapshot"
                    })
                if t.get('eod_source_plan'):
                    eod_plan = t['eod_source_plan']
                    fam = eod_plan['source_family']
                    actual_ops.append({
                        "target_id": tid,
                        "source_family": fam,
                        "operation_type": "official_eod",
                        "timing_class": "official_eod" if fam.endswith("OPENAPI") else "official_statistics_eod"
                    })
            # Filter out session-level ops (target_id starts with '_') from the
            # preview's planned_operations before comparing against plan-derived ops.
            planned_ops = [op for op in preview.get('planned_operations', []) if not str(op.get('target_id', '')).startswith('_')]
            mismatch = False
            for aop in actual_ops:
                found = False
                for pop in planned_ops:
                    if (aop["target_id"] == pop.get("target_id") and
                        aop["source_family"] == pop.get("source_family") and
                        aop["operation_type"] == pop.get("operation_type") and
                        aop["timing_class"] == pop.get("timing_class")):
                        found = True
                        break
                if not found:
                    mismatch = True
                    break
            if mismatch:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'preview_plan_mismatch', 'blocking':True}],artifact_root_path,write=True,preview=preview,approval=approval)
                
            # 4. 預防 Replay 檢查與 Claim
            claim_root = AUTHORIZATION_CONSUMPTION_ROOT
            claim_key = sha256_json({'preview_id': preview['preview_id'], 'request_id': request['request_id']})
            claim_path = claim_root / f"{claim_key}.json"
            try:
                claim_content = json.dumps({
                    'schema_version': 'm8r_phase_c_conversation_approval_consumption_receipt.v1',
                    'preview_id': preview['preview_id'],
                    'request_id': request['request_id'],
                    'claimed_at_utc': started,
                    'status': 'claimed'
                }, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
                atomic_create_text_exclusive(claim_root, f"{claim_key}.json", claim_content)
            except FilesystemSafetyError as exc:
                if exc.code == 'already_consumed_or_replayed' or claim_path.exists():
                    return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'authorization_replayed'}],artifact_root_path,write=True,preview=preview,approval=approval)
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'authorization_consumption_failed','detail':str(exc)[:120]}],artifact_root_path,write=True,preview=preview,approval=approval)
            except Exception as exc:
                return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'authorization_consumption_failed','detail':str(exc)[:120]}],artifact_root_path,write=True,preview=preview,approval=approval)

            # --- AUTHORIZATION BOUNDARY ---
            # All network calls and persistent writes must occur after this point.
            # The anti-replay claim above is the last authorization gate.

            # Resolve official calendar and natural disaster closure feed.
            # These network calls are declared in the preview as session-level ops.
            try:
                from scripts.m8r_eod_expected_trade_date import parse_taipei_datetime
                ref_dt = parse_taipei_datetime(started)
            except Exception:
                from datetime import datetime
                from zoneinfo import ZoneInfo
                ref_dt = datetime.now(ZoneInfo("Asia/Taipei"))
            calendar_artifact, calendar_load_mode = _load_production_calendar(ref_dt, authorized_root=artifact_root_path)
            try:
                from scripts.m8a_ncdr_dgpa_closure_cap import fetch_and_parse_closure_feed
                parsed_feed = fetch_and_parse_closure_feed()
                closure_events = parsed_feed.get("events")
            except Exception:
                closure_events = None

            session_results = []
            if calendar_artifact is not None:
                session_results.append({
                    'operation_id': 'op-_session-TWSE_OPENAPI-calendar',
                    'target_id': '_session',
                    'source_family': 'TWSE_OPENAPI',
                    'status': calendar_load_mode if calendar_load_mode != "network_fetch" else "network_success"
                })
            else:
                session_results.append({
                    'operation_id': 'op-_session-TWSE_OPENAPI-calendar',
                    'target_id': '_session',
                    'source_family': 'TWSE_OPENAPI',
                    'status': 'unresolved_fallback'
                })
            
            if closure_events is not None:
                session_results.append({
                    'operation_id': 'op-_session-NCDR_DGPA_CLOSURE_CAP-closure',
                    'target_id': '_session',
                    'source_family': 'NCDR_DGPA_CLOSURE_CAP',
                    'status': 'network_success'
                })
            else:
                session_results.append({
                    'operation_id': 'op-_session-NCDR_DGPA_CLOSURE_CAP-closure',
                    'target_id': '_session',
                    'source_family': 'NCDR_DGPA_CLOSURE_CAP',
                    'status': 'unresolved_fallback'
                })

            source_data, group_results = _execute_source_groups(plan, request, executors or {})

        else:
            # 舊版 Authorization 驗證流程
            if not authorization: return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'authorization_required'}],artifact_root_path,write=False)
            av=validate_authorization(authorization,request=request,plan=plan,bundle_type=bundle_type,now_utc=started,require_network=True)
            if not av['valid']: return _result(run_id,mode,started,utc_now(),request,plan,authorization,[],None,'authorization_failed',av['issues'],artifact_root_path,write=True)
            claim=_claim_authorization(authorization, plan, artifact_root, started)
            if not claim['valid']: return _result(run_id,mode,started,utc_now(),request,plan,authorization,[],None,'authorization_failed',claim['issues'],artifact_root_path,write=True)
            source_data, group_results = _execute_source_groups(plan,request,executors or {})
    else:
        source_data=fixture_source_data or {}; group_results=_fixture_group_results(plan, source_data, started)
        
    observations=[]; target_results=[]; normalize_issues=[]; eod_issues=[]
    if phase_c_active and mode == 'execute':
        target_results.extend(session_results)
    for t in plan['targets']:
        tid=t['target_id']
        if t['identity_status']!='resolved':
            target_results.append({'target_id':tid,'status':'skipped','reason_code':'identity_unresolved'}); continue
        srcs=(source_data.get('targets') or {}).get(tid,{})
        target_eod_diagnostics=(source_data.get('_target_eod_diagnostics') or {}).get(tid,{})
        
        if phase_c_active:
            # Phase C 啟用時：完全由 registry 與 plan 驅動的動態處理
            live_fam = t.get('current_source_plan', {}).get('source_family')
            is_fallback = False
            fam = t['eod_source_plan'].get('source_family') if t.get('eod_source_plan') else None
            rows = srcs.get(fam) if fam else None
            
            if live_fam and not srcs.get(live_fam) and fam and rows:
                is_fallback = True
                
            if bundle_type=='snapshot' and live_fam and srcs.get(live_fam):
                obs=_normalize_checked(live_fam,srcs[live_fam],t,started, calendar_artifact, closure_events)
                if obs: 
                    observations.append(obs)
                    target_results.append({
                        'target_id':tid,
                        'source_family':live_fam,
                        'status':'normalized',
                        'planned_operation_id': f"op-{tid}-{live_fam}",
                        'actual_operation_id': f"op-{tid}-{live_fam}",
                        'fallback_from_operation_id': None
                    })
                else: 
                    normalize_issues.append({'code':'source_identity_mismatch','target_id':tid,'source_family':live_fam})
                
            if rows:
                if not isinstance(rows,list): rows=[rows]
                kept=0
                for row in rows:
                    obs=_normalize_checked(fam,row,t,started, calendar_artifact, closure_events)
                    if obs: observations.append(obs); kept+=1
                    else: normalize_issues.append({'code':'source_identity_mismatch','target_id':tid,'source_family':fam})
                if is_fallback:
                    target_result={
                        'target_id':tid,
                        'source_family':fam,
                        'status':'fallback_success',
                        'fallback_used':True,
                        'requested_source_family':live_fam,
                        'actual_source_family':fam,
                        'requested_timing_class':'liveish_intraday_snapshot',
                        'actual_timing_class':'official_eod',
                        'fallback_reason':'liveish_observation_unavailable',
                        'row_count':kept,
                        'planned_operation_id': f"op-{tid}-{live_fam}",
                        'actual_operation_id': f"op-{tid}-{fam}",
                        'fallback_from_operation_id': f"op-{tid}-{live_fam}"
                    }
                else:
                    target_result={
                        'target_id':tid,
                        'source_family':fam,
                        'status':'normalized' if kept else 'failed',
                        'row_count':kept,
                        'planned_operation_id': f"op-{tid}-{fam}",
                        'actual_operation_id': f"op-{tid}-{fam}",
                        'fallback_from_operation_id': None
                    }
                _attach_eod_target_diagnostics(target_result, target_eod_diagnostics.get(fam), eod_issues)
                target_results.append(target_result)
            elif not live_fam or not srcs.get(live_fam):
                target_result={
                    'target_id':tid,
                    'status':'source_unavailable',
                    'reason_code':'missing_fixture_or_source_result'
                }
                if fam_diag := target_eod_diagnostics.get(fam):
                    target_result['source_family']=fam
                    _attach_eod_target_diagnostics(target_result, fam_diag, eod_issues)
                    rejected = fam_diag.get('rejected_rows') or []
                    if rejected:
                        first = rejected[0]
                        target_result.update({'status':'failed','reason_code':first['reason_code']})
                        target_result['rejection_reason_codes'] = sorted({r['reason_code'] for r in rejected})[:8]
                    elif fam_diag.get('batch_status') in {'date_mismatch','source_error','schema_drift'}:
                        target_result.update({'status':'failed','reason_code':fam_diag['batch_status']})
                    elif fam_diag.get('batch_status') == 'empty_non_trading_day':
                        target_result['reason_code']='empty_non_trading_day'
                target_results.append(target_result)
            elif fam_diag := target_eod_diagnostics.get(fam):
                rejected=fam_diag.get('rejected_rows') or []
                batch_status=fam_diag.get('batch_status')
                if rejected or batch_status in {'partial_source_success','date_mismatch','source_error','schema_drift'}:
                    target_result={'target_id':tid,'source_family':fam,'status':'failed' if rejected or batch_status in {'date_mismatch','source_error','schema_drift'} else 'source_unavailable'}
                    if rejected:
                        target_result['reason_code']=rejected[0]['reason_code']
                    elif batch_status:
                        target_result['reason_code']=batch_status
                    _attach_eod_target_diagnostics(target_result,fam_diag,eod_issues)
                    target_results.append(target_result)
        else:
            # 傳統模式：完全回退到 PR #157 原始的硬編碼處理邏輯
            if bundle_type=='snapshot' and srcs.get('TWSE_MIS'):
                obs=_normalize_checked('TWSE_MIS',srcs['TWSE_MIS'],t,started, calendar_artifact, closure_events)
                if obs: observations.append(obs); target_results.append({'target_id':tid,'source_family':'TWSE_MIS','status':'normalized'})
                else: normalize_issues.append({'code':'source_identity_mismatch','target_id':tid,'source_family':'TWSE_MIS'})
            for fam in ('TWSE_OPENAPI','TPEX_OPENAPI'):
                rows=srcs.get(fam)
                if rows:
                    if not isinstance(rows,list): rows=[rows]
                    kept=0
                    for row in rows:
                        obs=_normalize_checked(fam,row,t,started, calendar_artifact, closure_events)
                        if obs: observations.append(obs); kept+=1
                        else: normalize_issues.append({'code':'source_identity_mismatch','target_id':tid,'source_family':fam})
                    is_fallback=(not srcs.get('TWSE_MIS')) and (fam in ('TWSE_OPENAPI','TPEX_OPENAPI'))
                    if is_fallback:
                        target_result={'target_id':tid,'source_family':fam,'status':'fallback_success','fallback_used':True,'requested_source_family':'TWSE_MIS','actual_source_family':fam,'requested_timing_class':'liveish_intraday_snapshot','actual_timing_class':'official_eod','fallback_reason':'liveish_observation_unavailable','row_count':kept}
                    else:
                        target_result={'target_id':tid,'source_family':fam,'status':'normalized' if kept else 'failed','row_count':kept}
                    _attach_eod_target_diagnostics(target_result,target_eod_diagnostics.get(fam),eod_issues)
                    target_results.append(target_result)
                elif not srcs.get('TWSE_MIS'):
                    target_result={'target_id':tid,'status':'source_unavailable','reason_code':'missing_fixture_or_source_result'}
                    if fam_diag := target_eod_diagnostics.get(fam):
                        target_result['source_family']=fam
                        _attach_eod_target_diagnostics(target_result,fam_diag,eod_issues)
                        rejected=fam_diag.get('rejected_rows') or []
                        if rejected:
                            target_result.update({'status':'failed','reason_code':rejected[0]['reason_code']})
                        elif fam_diag.get('batch_status') in {'date_mismatch','source_error','schema_drift'}:
                            target_result.update({'status':'failed','reason_code':fam_diag['batch_status']})
                        elif fam_diag.get('batch_status') == 'empty_non_trading_day':
                            target_result['reason_code']='empty_non_trading_day'
                    target_results.append(target_result)
                elif fam_diag := target_eod_diagnostics.get(fam):
                    rejected=fam_diag.get('rejected_rows') or []
                    batch_status=fam_diag.get('batch_status')
                    if rejected or batch_status in {'partial_source_success','date_mismatch','source_error','schema_drift'}:
                        target_result={'target_id':tid,'source_family':fam,'status':'failed' if rejected or batch_status in {'date_mismatch','source_error','schema_drift'} else 'source_unavailable'}
                        if rejected:
                            target_result['reason_code']=rejected[0]['reason_code']
                        elif batch_status:
                            target_result['reason_code']=batch_status
                        _attach_eod_target_diagnostics(target_result,fam_diag,eod_issues)
                        target_results.append(target_result)
            
    try:
        bundle=build_watchlist_snapshot_bundle(request=request,observations=observations,generated_at_utc=started) if bundle_type=='snapshot' else build_watchlist_performance_bundle(request=request,observations=observations,generated_at_utc=started)
        partial=any(c['coverage_state']!='usable' for c in bundle['coverage']['targets'])
        any_group_failed=any(g.get('status')=='failed' for g in group_results)
        any_group_partial=any(g.get('reason_code')=='partial_source_success' for g in group_results)
        status='success_with_partial_coverage' if partial or any_group_failed or any_group_partial or normalize_issues or eod_issues else 'success'; issues=normalize_issues+eod_issues
        if not observations and any_group_failed: status='source_execution_failed'
    except Exception as exc:
        bundle=None; status='bundle_validation_failed'; issues=normalize_issues+[{'code':'bundle_validation_failed','detail':str(exc)[:160]}]
        
    return _result(run_id,mode,started,started if mode != 'execute' else utc_now(),request,plan,authorization if mode=='execute' and not phase_c_active else None,observations,bundle,status,issues,artifact_root_path,target_results=target_results,source_execution_summary={'planned_source_call_groups':plan.get('source_call_groups',[]),'group_results':group_results,'network_calls_performed':mode=='execute','network_default_enabled':False,'polling':False,'scheduler':False},write=True,preview=preview,approval=approval)

def _claim_authorization(auth, plan, artifact_root, now):
    root=AUTHORIZATION_CONSUMPTION_ROOT
    key=sha256_json({'authorization_id':auth['authorization_id'],'one_shot_nonce':auth['one_shot_nonce'],'request_hash':plan['request_hash']})
    path=root/(key+'.json')
    receipt={'schema_version':'m8r_03d_authorization_consumption_receipt.v1','authorization_id':auth['authorization_id'],'one_shot_nonce_hash':sha256_json(auth['one_shot_nonce']),'request_hash':plan['request_hash'],'plan_id':plan['plan_id'],'claimed_at_utc':now,'status':'claimed'}
    
    try:
        content = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
        atomic_create_text_exclusive(root, f"{key}.json", content)
        return {'valid':True,'receipt_path':str(path),'issues':[]}
    except FilesystemSafetyError as exc:
        if exc.code == 'already_consumed_or_replayed':
            return {'valid':False,'issues':[{'code':'authorization_replayed'}]}
        return {'valid':False,'issues':[{'code':'authorization_consumption_failed','detail':str(exc)[:120]}]}
    except Exception as exc:
        return {'valid':False,'issues':[{'code':'authorization_consumption_failed','detail':str(exc)[:120]}]}

def _fixture_group_results(plan, source_data, started):
    out=[]
    for g in plan.get('source_call_groups',[]):
        count=0
        for tid in g['target_ids']:
            rows=(source_data.get('targets') or {}).get(tid,{}).get(g['source_family'])
            count += len(rows) if isinstance(rows,list) else (1 if rows else 0)
        out.append({'source_family':g['source_family'],'target_ids':g['target_ids'],'started_at_utc':started,'completed_at_utc':started,'status':'success' if count else 'failed','observation_count':count,'reason_code':None if count else 'fixture_source_unavailable'})
    return out

# 集中式來源執行與歸一化適配器註冊表 (Blocker 2 修正)
SOURCE_ADAPTERS = {
    'TWSE_MIS': lambda plan, request, g: _live_twse_mis(plan, request, g),
    'TWSE_OPENAPI': lambda plan, request, g: _live_eod(plan, g, execute_twse_official_eod_adapter, 'TWSE:'),
    'TPEX_OPENAPI': lambda plan, request, g: _live_eod(plan, g, execute_tpex_official_eod_adapter, 'TPEX:'),
}

NORMALIZERS = {
    'TWSE_MIS': normalize_twse_mis_watchlist_observation,
    'TWSE_OPENAPI': normalize_twse_openapi_watchlist_observation,
    'TPEX_OPENAPI': normalize_tpex_openapi_watchlist_observation,
}

def _execute_source_groups(plan, request, executors):
    data={'targets':{},'_target_eod_diagnostics':{}}; results=[]
    for g in plan.get('source_call_groups',[]):
        fam=g['source_family']; start=utc_now(); count=0; status='success'; reason=None
        try:
            if fam in executors:
                res=executors[fam](g['target_ids'], plan=plan, request=request, source_call_group=g)
            elif fam in SOURCE_ADAPTERS:
                res=SOURCE_ADAPTERS[fam](plan, request, g)
            else: raise ValueError('unsupported_source_family')
            for tid, srcs in (res.get('targets') or {}).items():
                for sf, rows in srcs.items():
                    data['targets'].setdefault(tid,{})[sf]=rows
                    count += len(rows) if isinstance(rows,list) else (1 if rows else 0)
            diagnostics=res.get('_eod_adapter_diagnostics')
            if isinstance(diagnostics,dict):
                projected=dict(diagnostics)
                for tid in g.get('target_ids',[]):
                    data['_target_eod_diagnostics'].setdefault(tid,{})[fam]=projected
                for tid, rejection in (res.get('_eod_rejected_by_target') or {}).items():
                    if tid in g.get('target_ids',[]):
                        data['_target_eod_diagnostics'].setdefault(tid,{})[fam]={**projected,'rejected_rows':rejection}
                for tid, validation in (res.get('_eod_validation_by_target') or {}).items():
                    if tid in g.get('target_ids',[]):
                        current=data['_target_eod_diagnostics'].setdefault(tid,{}).get(fam,projected)
                        data['_target_eod_diagnostics'][tid][fam]={**current,'observation_field_validation':validation}
                results.append({'source_family':fam,'target_ids':g['target_ids'],'started_at_utc':start,'completed_at_utc':utc_now(),'status':_eod_group_status(diagnostics),'observation_count':count,'reason_code':_eod_group_reason(diagnostics),'adapter_diagnostics':projected})
                continue
        except Exception as exc:
            status='failed'; reason=str(exc).splitlines()[0][:80]
        results.append({'source_family':fam,'target_ids':g['target_ids'],'started_at_utc':start,'completed_at_utc':utc_now(),'status':status,'observation_count':count,'reason_code':reason})
    return data, results

def _live_twse_mis(plan, request, g):
    byid={t['target_id']:t for t in plan['targets']}
    wl={'schema_version':'m5n_watchlist.v1','watchlist_id':request['persistent_watchlist_reference']['watchlist_id'],'items':[{'symbol':byid[tid]['security_code'],'market':'twse' if byid[tid]['market']=='TWSE' else 'tpex_otc','instrument_type':byid[tid]['instrument_type'],'enabled':True} for tid in g['target_ids']]}
    live=execute_live_observation(wl,write_latest=False); out={'targets':{}}
    for obs in live.get('observations',[]):
        tid=('TPEX:' if obs.get('market') in MARKET_ALIASES['TPEX'] else 'TWSE:')+str(obs.get('symbol'))
        out['targets'].setdefault(tid,{})['TWSE_MIS']=obs
    return out

def _live_eod(plan, g, fn, pref):
    byid={t['target_id']:t for t in plan['targets']}; syms=[byid[tid]['security_code'] for tid in g['target_ids']]
    res=fn(syms); out={'targets':{}}
    for obs in res.get('observations',[]): out['targets'].setdefault(pref+obs.get('symbol'),{})[g['source_family']]=obs
    out['_eod_adapter_diagnostics']=_project_eod_diagnostics(res)
    by_symbol={str(byid[tid]['security_code']):tid for tid in g['target_ids']}
    rejected_by_target={}
    for rejected in res.get('rejected_rows',[]) if isinstance(res.get('rejected_rows'),list) else []:
        if not isinstance(rejected,dict): continue
        symbol=rejected.get('symbol')
        tid=by_symbol.get(str(symbol)) if symbol is not None else None
        projection=_project_eod_rejected_row(rejected)
        if tid is not None:
            rejected_by_target.setdefault(tid,[]).append(projection)
    if rejected_by_target:
        out['_eod_rejected_by_target']={tid:sorted(rows,key=lambda row:(row['reason_code'],tuple(row['invalid_fields'])))[:8] for tid,rows in rejected_by_target.items()}
    validation_by_target={}
    for obs in res.get('observations',[]) if isinstance(res.get('observations'),list) else []:
        if not isinstance(obs,dict): continue
        tid=by_symbol.get(str(obs.get('symbol'))) if obs.get('symbol') is not None else None
        validation=_project_eod_observation_validation(obs)
        if tid is not None and validation['invalid_fields']:
            validation_by_target.setdefault(tid,[]).append(validation)
    if validation_by_target:
        out['_eod_validation_by_target']={tid:sorted(rows,key=lambda row:(row['symbol'] or '',tuple(row['invalid_fields'])))[:8] for tid,rows in validation_by_target.items()}
    if res.get('source_status') != 'success' or res.get('batch_status') in {'source_error','schema_drift','date_mismatch'}:
        out['targets']={}
    return out


def _project_eod_rejected_row(row):
    validation=row.get('field_validation') if isinstance(row.get('field_validation'),dict) else {}
    invalid=[]
    missing=validation.get('missing')
    if isinstance(missing,list): invalid.extend(str(name) for name in missing if isinstance(name,str))
    for name,value in validation.items():
        if isinstance(value,dict) and value.get('valid') is False: invalid.append(str(name))
    return {'symbol':row.get('symbol')[:32] if isinstance(row.get('symbol'),str) else None,
            'reason_code':str(row.get('reason_code') or 'source_row_rejected')[:80],
            'invalid_fields':sorted({name[:80] for name in invalid})[:16]}


def _project_eod_observation_validation(row):
    validation=row.get('field_validation') if isinstance(row.get('field_validation'),dict) else {}
    invalid=[]
    for name,value in validation.items():
        if isinstance(value,dict) and value.get('valid') is False:
            reason=value.get('reason')
            invalid.append({'field':str(name)[:80],'reason_code':str(reason).split(':',1)[0][:40] if isinstance(reason,str) else 'invalid'})
    invalid.sort(key=lambda item:(item['field'],item['reason_code']))
    return {'symbol':row.get('symbol')[:32] if isinstance(row.get('symbol'),str) else None,
            'observation_status':str(row.get('observation_status') or 'unknown')[:24],
            'invalid_fields':invalid[:16]}


def _project_eod_diagnostics(result):
    if not isinstance(result,dict):
        return {'source_status':'error','batch_status':'source_error','adapter_result_invalid':True}
    def count(name):
        value=result.get(name)
        return value if isinstance(value,int) and not isinstance(value,bool) and value >= 0 else None
    raw_dates=result.get('reported_trade_dates')
    unique_dates=sorted({value for value in raw_dates if isinstance(value,str)}) if isinstance(raw_dates,list) else []
    dates=[value[:32] for value in unique_dates[:16]]
    rejected=result.get('rejected_rows')
    projected_rejections=[_project_eod_rejected_row(row) for row in rejected[:32] if isinstance(row,dict)] if isinstance(rejected,list) else []
    reasons=sorted({row['reason_code'] for row in projected_rejections})[:16]
    observations=result.get('observations')
    invalid_observations=[_project_eod_observation_validation(row) for row in observations if isinstance(row,dict)] if isinstance(observations,list) else []
    invalid_observations=[row for row in invalid_observations if row['invalid_fields']][:32]
    return {
        'source_id':str(result.get('source_id') or '')[:80],
        'endpoint_contract_id':str(result.get('endpoint_contract_id') or '')[:120],
        'source_status':str(result.get('source_status') or 'unknown')[:40],
        'batch_status':str(result.get('batch_status') or 'unknown')[:40],
        'row_count_received':count('row_count_received'),
        'row_count_examined':count('row_count_examined'),
        'row_count_retained':count('row_count_retained'),
        'row_count_rejected':count('row_count_rejected'),
        'reported_trade_dates':dates,
        'reported_trade_date_count':len(unique_dates),
        'rejection_reason_codes':reasons,
        'rejected_rows':projected_rejections,
        'partial_observations':invalid_observations,
        'caveat_count':len(result.get('caveats')) if isinstance(result.get('caveats'),list) else 0,
        'caveat_codes':_project_eod_caveat_codes(result.get('caveats')),
        'http_status':result.get('http_status') if isinstance(result.get('http_status'),int) else None,
    }


def _project_eod_caveat_codes(caveats):
    if not isinstance(caveats,list): return []
    codes=set()
    for caveat in caveats[:32]:
        if not isinstance(caveat,str): continue
        lower=caveat.lower()
        if 'mixed trade dates' in lower: codes.add('mixed_trade_dates')
        elif 'tradevolume unit' in lower: codes.add('volume_unit_caveat')
        elif 'top-level response was not an array' in lower: codes.add('top_level_response_not_array')
        elif 'classification' in lower or 'unclassified' in lower: codes.add('instrument_classification_caveat')
        else: codes.add('source_caveat_present')
    return sorted(codes)[:8]


def _eod_group_status(diagnostics):
    source_status=diagnostics.get('source_status')
    batch_status=diagnostics.get('batch_status')
    if source_status != 'success' or batch_status in {'source_error','schema_drift','date_mismatch'}:
        return 'failed'
    if batch_status in {'successful_eod_batch','partial_source_success','empty_non_trading_day'}:
        return 'success'
    if diagnostics.get('partial_observations'):
        return 'success'
    return 'failed'


def _eod_group_reason(diagnostics):
    status=diagnostics.get('batch_status')
    if diagnostics.get('source_status') != 'success' and status not in {'source_error','schema_drift'}:
        return 'source_error'
    if diagnostics.get('partial_observations'): return 'partial_source_success'
    if status in {'partial_source_success','empty_non_trading_day'}: return status
    return None if status == 'successful_eod_batch' else status


def _attach_eod_target_diagnostics(target_result, diagnostic, issues):
    if not isinstance(diagnostic,dict): return
    target_result['source_diagnostics']={key:value for key,value in diagnostic.items() if key != 'rejected_rows'}
    rejected=diagnostic.get('rejected_rows') or []
    if rejected:
        target_result['rejection_reason_codes']=sorted({row['reason_code'] for row in rejected})[:8]
        target_result['rejected_row_diagnostics']=rejected[:8]
    batch_status=diagnostic.get('batch_status')
    invalid_fields=diagnostic.get('observation_field_validation') or []
    if invalid_fields:
        target_result['field_validation_diagnostics']=invalid_fields
    issue_code=batch_status if batch_status in {'partial_source_success','date_mismatch','source_error','schema_drift'} else ('partial_source_success' if invalid_fields else None)
    if issue_code:
        issues.append({'code':issue_code,'source_family':target_result.get('source_family'),'target_id':target_result.get('target_id'),'reported_trade_dates':diagnostic.get('reported_trade_dates',[]),'rejection_reason_codes':target_result.get('rejection_reason_codes',[]),'invalid_field_names':sorted({item['field'] for row in invalid_fields for item in row['invalid_fields']})[:16]})

def _normalize_checked(fam, row, target, retrieved_at, calendar_artifact=None, closure_events=None):
    symbol=str(row.get('symbol') or row.get('c') or row.get('safe_fields',{}).get('symbol') or '')
    market=row.get('market') or row.get('exchange') or row.get('ex')
    expected_market=target.get('market')
    if symbol != str(target.get('security_code')): return None
    expected_market_normalized = 'TWSE' if expected_market in ('TWSE', 'listed') else 'TPEX'
    if market is not None and str(market) not in MARKET_ALIASES.get(expected_market_normalized, set()): return None
    
    if fam in NORMALIZERS:
        if fam in {'TWSE_OPENAPI', 'TPEX_OPENAPI'}:
            return NORMALIZERS[fam](row,target,reference_clock_utc=retrieved_at, calendar_artifact=calendar_artifact, closure_events=closure_events)
        else:
            return NORMALIZERS[fam](row,target,reference_clock_utc=retrieved_at)
    return None

def _result(run_id,mode,started,completed,request,plan,auth,observations,bundle,status,issues,artifact_root_path,target_results=None,source_execution_summary=None,write=True,preview=None,approval=None):
    artifact_root_path = artifact_root_path if isinstance(artifact_root_path, Path) else _safe_root(artifact_root_path)
    root=safe_destination(artifact_root_path, run_id, create_parent=True).path
    paths={}; final_status=status; final_issues=list(issues or [])
    if write:
        try:
            _write_json(artifact_root_path,root/'validated_request.json',request); paths['validated_request']=str(root/'validated_request.json')
            _write_json(artifact_root_path,root/'execution_plan.json',plan); paths['execution_plan']=str(root/'execution_plan.json')
            if auth: _write_json(artifact_root_path,root/'authorization.json',auth); paths['authorization']=str(root/'authorization.json')
            if preview: _write_json(artifact_root_path,root/'execution_preview.json',preview); paths['execution_preview']=str(root/'execution_preview.json')
            if approval: _write_json(artifact_root_path,root/'approval_record.json',approval); paths['approval']=str(root/'approval_record.json')
            _write_json(artifact_root_path,root/'normalized_observations.json',observations); paths['normalized_observations']=str(root/'normalized_observations.json')
            if bundle:
                name='watchlist_snapshot_bundle.json' if bundle['schema_version'].endswith('snapshot_bundle.v1') else 'watchlist_performance_bundle.json'
                _write_json(artifact_root_path,root/name,bundle); paths['bundle']=str(root/name)
        except Exception as exc:
            paths={}; final_status='bundle_validation_failed' if status in {'success','success_with_partial_coverage'} else status
            final_issues.append({'code':'artifact_write_failed','detail':str(exc)[:120]})
            
    summary=source_execution_summary or {'planned_source_call_groups':plan.get('source_call_groups',[]),'group_results':[],'network_default_enabled':False,'polling':False,'scheduler':False}
    result={'schema_version':RESULT_SCHEMA_VERSION,'run_id':run_id,'authorization_id':(auth or {}).get('authorization_id'),'request_id':request.get('request_id'),'request_hash':plan.get('request_hash'),'plan_id':plan.get('plan_id'),'mode':mode,'started_at_utc':started,'completed_at_utc':completed,'source_execution_summary':summary,'target_results':target_results or [],'observation_count':len(observations),'bundle_artifact':paths.get('bundle'),'status':final_status,'issues':final_issues,'artifact_paths':paths}
    
    if preview:
        planned_op_ids = [op["operation_id"] for op in preview.get("planned_operations", [])]
        actual_op_ids = []
        failed_op_ids = []
        skipped_op_ids = []
        fallback_op_ids = []
        
        for pop in preview.get("planned_operations", []):
            op_id = pop["operation_id"]
            tid = pop["target_id"]
            fam = pop["source_family"]
            matched_tr = [tr for tr in (target_results or []) if tr.get("target_id") == tid and tr.get("source_family") == fam]
            if matched_tr:
                tr_status = matched_tr[0].get("status")
                if tr_status in {"normalized", "network_success", "cache_hit"}:
                    actual_op_ids.append(op_id)
                elif tr_status in {"fallback_success", "unresolved_fallback"}:
                    actual_op_ids.append(op_id)
                    fallback_op_ids.append(op_id)
                elif tr_status in {"failed", "network_failed"}:
                    failed_op_ids.append(op_id)
                else:
                    skipped_op_ids.append(op_id)
            else:
                skipped_op_ids.append(op_id)
                
        result["preview_id"] = preview.get("preview_id")
        result["execution_audit"] = {
            "preview_id": preview.get("preview_id"),
            "request_id": request.get("request_id"),
            "approval_mode": "conversation_explicit_approval",
            "approval_status": (approval or {}).get("approval_status"),
            "planned_operation_ids": planned_op_ids,
            "actual_operation_ids": actual_op_ids,
            "skipped_operation_ids": skipped_op_ids,
            "fallback_operation_ids": fallback_op_ids,
            "failed_operation_ids": failed_op_ids,
            "unexpected_operation_ids": []
        }
        try:
            policy_path = Path("docs/data_capabilities/m8r_03e_phase_c_activation_policy.json")
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            ret = policy["artifact_retention"]
            retention_days = ret["default_retention_days"]
            pin_sup = ret["manual_pin_supported"]
            del_sup = ret["manual_delete_supported"]
            behavior = ret["expired_artifact_behavior"]
            auto_clean = ret["automatic_cleanup_scheduler_enabled"]
        except Exception:
            retention_days = 30
            pin_sup = True
            del_sup = True
            behavior = "eligible_for_cleanup"
            auto_clean = False
 
        result["retention_policy"] = {
            "default_retention_days": retention_days,
            "manual_pin_supported": pin_sup,
            "manual_delete_supported": del_sup,
            "expired_artifact_behavior": behavior,
            "automatic_cleanup_scheduler_enabled": auto_clean
        }
        
    if write and paths:
        try: _write_json(artifact_root_path,root/'execution_result.json',result)
        except Exception as exc: result['status']='bundle_validation_failed'; result['issues'].append({'code':'artifact_write_failed','detail':str(exc)[:120]})
    return result
