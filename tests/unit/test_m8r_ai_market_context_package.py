from __future__ import annotations

import json, shutil
from copy import deepcopy
from pathlib import Path
import pytest

from scripts.m8r_ai_market_context_package import *

NOW="2026-07-15T01:02:03Z"

def obs(source="TWSE_MIS", timing="liveish_intraday_snapshot", market="TWSE", symbol="2330", typ="equity", ctx="liveish_observation", cur="fresh_intraday_snapshot", ident=None):
    sf={"last":"100","currentness":{"status":cur}}
    if ident: sf["contract_identity"]=ident
    return {"source_id":source,"source_family":source,"context_type":ctx,"authority_level":"official_undocumented" if source.endswith("MIS") else "official_documented","timing_class":timing,"source_timestamp":"2026-07-15T01:00:00Z","retrieved_at_utc":NOW,"market":market,"symbol":symbol,"instrument_type":typ,"currentness":{"status":cur},"safe_fields":sf,"caveats":[]}

def result(status="ready_with_caveats", receipt_id="r1", plan_hash="h1", missing=None, ops=None, targets=None, retention=True, core_status="built"):
    if ops is None:
        ops=[{"operation_id":"op1","target_id":"TWSE:equity:2330","context_type":"liveish_observation","source_family":"TWSE_MIS","operation_class":"planned_network_fetch","status":"succeeded","network_attempted":True,"source_observation":obs(),"currentness":{"status":"fresh_intraday_snapshot"},"issues":[]}]
    return {"schema_version":"m8r_market_context_orchestration_result.v1","execution_status":status,"execution_receipt":{"schema_version":"m8r_market_context_execution_receipt.v1","receipt_id":receipt_id,"plan_id":"p1","plan_hash":plan_hash,"approval_id":"a1","approved_output_scope":{"artifact_root":"research/m8r/test"},"execution_started_at_utc":NOW,"execution_finished_at_utc":NOW,"approval_consumed":True,"bounded_retention":retention,"raw_payload_retained":False if retention else True,"full_market_retained_output":False,"approved_target_count":len(targets or [1]),"approved_operation_count":len(ops),"successful_context_count":sum(1 for o in ops if o.get('status')=='succeeded' and o.get('operation_class')=='planned_network_fetch'),"missing_context_count":len(missing or []),"network_operations_attempted":sum(1 for o in ops if o.get('network_attempted')),"local_operations_attempted":sum(1 for o in ops if o.get('operation_class','').startswith('local_')),"package_status":status},"operation_results":ops,"missing_context":missing or [],"m8_context_core_status":{"status":core_status},"approval_state":{"approval_id":"a1","approval_status":"consumed"}}

def build(r, t=NOW): return build_ai_market_context_package(r, generated_at_utc=t)

def test_identity_determinism_and_hash_boundaries():
    p1=build(result(), "2026-07-15T01:02:03Z"); p2=build(result(), "2026-07-15T02:02:03Z")
    assert p1["package_id"]==p2["package_id"] and p1["integrity"]["package_hash"]==p2["integrity"]["package_hash"]
    assert build(result(plan_hash="h2"))["package_id"] != p1["package_id"]
    assert build(result(receipt_id="r2"))["package_id"] != p1["package_id"]
    r=result(ops=list(reversed(result()["operation_results"])))
    assert build(r)["package_id"]==p1["package_id"]

def test_status_rules_missing_blocked_and_unsafe_retention():
    miss=[{"target_id":"TWSE:equity:2330","context_type":"official_eod_reference","planned_source_family":"TWSE_OPENAPI","reason_code":"source_execution_failed","operation_status":"failed"}]
    assert build(result(status="partial", missing=miss))["package_status"]=="partial"
    assert build(result(status="blocked", ops=[], missing=miss))["package_status"]=="blocked"
    assert build(result(retention=False))["package_status"]=="blocked"
    assert any(c["code"]=="unsafe_upstream_retention_contract" for c in build(result(retention=False))["caveats"])

def test_source_semantics_currentness_and_caveats():
    ops=[]
    for i,(src,timing,ctx,cur) in enumerate([("TWSE_MIS","liveish_intraday_snapshot","liveish_observation","fresh_intraday_snapshot"),("TWSE_OPENAPI","official_eod","official_eod_reference","official_eod_reference"),("TPEX_OPENAPI","official_eod","official_eod_reference","official_eod_reference"),("TAIFEX_MIS","liveish_intraday_snapshot","liveish_observation","source_specific_currentness_unresolved"),("TAIFEX_OPENAPI","official_statistics_eod","official_statistical_reference","stale_official_statistics_eod")]):
        market="TAIFEX" if src.startswith("TAIFEX") else ("TPEX" if src.startswith("TPEX") else "TWSE")
        typ="future" if market=="TAIFEX" else "equity"; symbol="TXF" if market=="TAIFEX" else "2330"
        ident={"expiry":"202607","contract_type":"monthly","session":"regular"} if market=="TAIFEX" else None
        ops.append({"operation_id":f"op{i}","target_id":f"{market}:{typ}:{symbol}","context_type":ctx,"source_family":src,"operation_class":"planned_network_fetch","status":"succeeded","network_attempted":True,"source_observation":obs(src,timing,market,symbol,typ,ctx,cur,ident),"currentness":{"status":cur},"issues":[]})
    pkg=build(result(ops=ops, targets=[1,2,3]))
    timing={c['source_family']:c['timing_class'] for c in pkg['source_contexts']}
    assert timing['TWSE_MIS']=='liveish_intraday_snapshot' and timing['TWSE_OPENAPI']=='official_eod'
    assert timing['TPEX_OPENAPI']=='official_eod' and timing['TAIFEX_MIS']=='liveish_intraday_snapshot' and timing['TAIFEX_OPENAPI']=='official_statistics_eod'
    assert pkg['currentness_summary']['overall_status']=='mixed'
    assert {'source_stale','currentness_unknown','official_eod_not_intraday','liveish_not_exchange_official_realtime'} <= {c['code'] for c in pkg['caveats']}

def test_taifex_identity_future_option_and_missing_blocks_validation():
    ident={"expiry":"202607","contract_type":"monthly","session":"regular"}
    pkg=build(result(ops=[{"operation_id":"op1","target_id":"TAIFEX:future:TXF","context_type":"liveish_observation","source_family":"TAIFEX_MIS","operation_class":"planned_network_fetch","status":"succeeded","network_attempted":True,"source_observation":obs("TAIFEX_MIS","liveish_intraday_snapshot","TAIFEX","TXF","future",ident=ident),"currentness":{"status":"fresh_intraday_snapshot"},"issues":[]}]))
    assert pkg['targets'][0]['derivative_identity']['expiry']=='202607'
    opt={"expiry":"202607","contract_type":"monthly","session":"regular","underlying":"TXO","strike":"21000","call_put":"C"}
    pkg2=build(result(ops=[{"operation_id":"op1","target_id":"TAIFEX:option:TXO","context_type":"liveish_observation","source_family":"TAIFEX_MIS","operation_class":"planned_network_fetch","status":"succeeded","network_attempted":True,"source_observation":obs("TAIFEX_MIS","liveish_intraday_snapshot","TAIFEX","TXO","option",ident=opt),"currentness":{"status":"fresh_intraday_snapshot"},"issues":[]}]))
    assert pkg2['targets'][0]['derivative_identity']['strike']=='21000'
    bad=deepcopy(pkg); bad['targets'][0]['derivative_identity'].pop('expiry'); bad['integrity']['package_hash']=compute_ai_market_context_hash(build_ai_market_context_hash_scope(bad)); bad['package_id']='amc-'+bad['integrity']['package_hash'][:16]
    with pytest.raises(AIMarketContextPackageError): validate_ai_market_context_package(bad)

def test_missing_local_forbidden_and_views():
    ops=[{"operation_id":"lh","target_id":"TWSE:equity:2330","context_type":"source_health","source_family":None,"operation_class":"local_source_health_read","status":"succeeded","network_attempted":False,"source_observation":{"source_id":"LOCAL_SOURCE_HEALTH","source_family":"LOCAL_CONTEXT","context_type":"source_health","retrieved_at_utc":NOW,"safe_fields":{"referenced_source_family":"TWSE_MIS","artifact_availability":"unknown","staleness_caveat":"not live"}}}, {"operation_id":"mc","target_id":"TWSE:equity:2330","context_type":"market_session_state","source_family":None,"operation_class":"local_market_clock_evaluation","status":"succeeded","network_attempted":False,"source_observation":{"source_id":"LOCAL_MARKET_CLOCK","source_family":"LOCAL_CONTEXT","context_type":"market_session_state","retrieved_at_utc":NOW,"safe_fields":{"target_market":"TWSE","market_session_state":"unresolved","calendar_caveat":"unresolved"}}}]
    pkg=build(result(status="ready_with_caveats", ops=ops))
    assert pkg['source_health_context'] and pkg['market_session_context']
    assert 'local_health_not_live_probe' in pkg['forbidden_interpretations'] and 'unresolved_session_not_open_or_closed' in pkg['forbidden_interpretations']
    assert {'compact','standard','diagnostic'} == set(pkg['conversation_views'])
    assert pkg['conversation_views']['compact']['package_id']==pkg['package_id']
    banned=['buying opportunity','will rise','complete market picture','all data is realtime']
    assert not any(b in json.dumps(pkg['conversation_views']).lower() for b in banned)

def test_raw_data_safety_and_safe_fields_allowed():
    r=result(); r['operation_results'][0]['source_observation']['safe_fields']['note']='raw word in value is ok'
    assert build(r)
    for key in ['raw_payload','authorization','cookie']:
        rr=result(); rr['operation_results'][0]['source_observation'][key]='x'
        with pytest.raises(AIMarketContextPackageError): build(rr)

def test_validation_tampering_dangling_counts_duplicate_and_unsafe_source():
    pkg=build(result())
    bad=deepcopy(pkg); bad['integrity']['package_hash']='bad'
    with pytest.raises(AIMarketContextPackageError): validate_ai_market_context_package(bad)
    bad=deepcopy(pkg); bad['targets'][0]['source_context_refs']=['missing']; bad['integrity']['package_hash']=compute_ai_market_context_hash(build_ai_market_context_hash_scope(bad)); bad['package_id']='amc-'+bad['integrity']['package_hash'][:16]
    with pytest.raises(AIMarketContextPackageError): validate_ai_market_context_package(bad)
    bad=deepcopy(pkg); bad['scope']['successful_context_count']=99; bad['integrity']['package_hash']=compute_ai_market_context_hash(build_ai_market_context_hash_scope(bad)); bad['package_id']='amc-'+bad['integrity']['package_hash'][:16]
    with pytest.raises(AIMarketContextPackageError): validate_ai_market_context_package(bad)
    bad=deepcopy(pkg); bad['source_contexts'].append(deepcopy(bad['source_contexts'][0])); bad['integrity']['package_hash']=compute_ai_market_context_hash(build_ai_market_context_hash_scope(bad)); bad['package_id']='amc-'+bad['integrity']['package_hash'][:16]
    with pytest.raises(AIMarketContextPackageError): validate_ai_market_context_package(bad)
    bad=deepcopy(pkg); bad['source_contexts'][0]['source_family']='UNSAFE'; bad['integrity']['package_hash']=compute_ai_market_context_hash(build_ai_market_context_hash_scope(bad)); bad['package_id']='amc-'+bad['integrity']['package_hash'][:16]
    with pytest.raises(AIMarketContextPackageError): validate_ai_market_context_package(bad)

def test_artifacts_receipt_scoped_atomic_existing_and_root_guard(tmp_path):
    pkg=build(result(receipt_id='rid-art'))
    root='research/m8r/test_ai_pkg_artifacts'; shutil.rmtree(root, ignore_errors=True); files=write_ai_market_context_artifacts(pkg, artifact_root=root)
    assert {Path(f).name for f in files} == {'ai_market_context_v1.json','ai_market_context_compact.json','ai_market_context_standard.json','ai_market_context_diagnostic.json'}
    assert all(Path(f).parent.name=='rid-art' for f in files)
    with pytest.raises(FileExistsError): write_ai_market_context_artifacts(pkg, artifact_root=str(root))
    with pytest.raises(OSError): write_ai_market_context_artifacts(pkg, artifact_root='frontend/public/x')

def test_boundary_no_network_or_product_surface_imports():
    text=Path('scripts/m8r_ai_market_context_package.py').read_text()
    banned_imports=['import requests','import urllib','import httpx','FastAPI','@app.','sqlite3']
    assert not any(b in text for b in banned_imports)
    assert PROD['production_executor_adapters_ready'] is False and PROD['production_live_execution_ready'] is False
