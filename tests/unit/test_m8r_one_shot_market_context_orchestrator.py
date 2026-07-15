from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.m8r_bounded_market_context_request import compile_market_context_execution_plan, build_approval_artifact
from scripts.m8r_one_shot_market_context_orchestrator import (
    preflight_approved_market_context_plan, execute_approved_market_context_plan,
    write_execution_artifacts, EXECUTOR_REGISTRY, InMemoryApprovalConsumptionStore, FilesystemApprovalConsumptionStore,
)

NOW="2026-07-15T00:00:00Z"

def req(targets, contexts=("liveish_observation",), sources=None, root="research/m8r/test"):
    r={"schema_version":"m8r_bounded_market_context_request.v1","request_id":"r1","targets":targets,"requested_context_types":list(contexts),"output_policy":{"artifact_root":root}}
    if sources: r["requested_source_families"]=list(sources)
    return r

def stock(symbol="2330", market="TWSE"):
    return {"market":market,"instrument_type":"equity","symbol":symbol}

def future(expiry="202607"):
    return {"market":"TAIFEX","instrument_type":"future","symbol":"TX","expiry":expiry,"contract_type":"monthly","session":"regular"}

def option(strike="20000", call_put="C"):
    return {"market":"TAIFEX","instrument_type":"option","symbol":"TXO","underlying":"TX","expiry":"202607","strike":strike,"call_put":call_put,"contract_type":"monthly","session":"regular"}

def plan_for(targets, contexts=("liveish_observation",), sources=None, root="research/m8r/test"):
    return compile_market_context_execution_plan(req(targets, contexts, sources, root), created_at_utc=NOW)

def approve(plan, **kw):
    kw.setdefault("single_use", False)
    return build_approval_artifact(plan, approved_at_utc=NOW, **kw)

class Fake:
    supports_exact_derivative_identity=True
    def __init__(self, status="succeeded", obs=None, returned_identity=None):
        self.calls=[]; self.status=status; self.obs=obs; self.returned_identity=returned_identity
    def __call__(self, *, operation, target, plan, execution_time_utc, allow_network):
        self.calls.append((operation,target))
        obs=self.obs or {"source_id":operation.get("source_family") or "TWSE_MIS","source_family":operation.get("source_family") or "TWSE_MIS","context_type":operation.get("context_type"),"authority_level":"official","timing_class":"liveish_intraday_snapshot","source_timestamp":execution_time_utc,"retrieved_at_utc":execution_time_utc,"market":(target or {}).get("market","TWSE").lower(),"symbol":(target or {}).get("symbol"),"instrument_type":(target or {}).get("instrument_type"),"safe_fields":{"last":"100"},"caveats":[]}
        return {"status":self.status,"network_attempted":operation.get("network_required",False),"source_observation":obs if self.status=="succeeded" else {},"returned_identity":self.returned_identity or {"expiry":((target or {}).get("derivative_identity") or {}).get("expiry"),"contract_type":"monthly"},"adapter_invocation_count":1,"issues":[] if self.status=="succeeded" else [{"code":"source_execution_failed"}]}

def registry(*pairs):
    r=dict(EXECUTOR_REGISTRY)
    for key, fake in pairs: r[key]=fake
    return r

def test_valid_approved_plan_passes_preflight_and_network_disabled_blocks_with_zero_calls():
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p); f=Fake()
    blocked=preflight_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),f)),execution_time_utc=NOW)
    assert blocked["preflight_status"]=="blocked" and blocked["issues"][0]["code"]=="network_execution_not_enabled"
    assert f.calls==[]
    ok=preflight_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),f)),execution_time_utc=NOW,allow_network=True)
    assert ok["preflight_status"]=="passed"

def test_modified_plan_stale_hash_and_wrong_approval_fail_before_execution():
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p); f=Fake()
    p2=json.loads(json.dumps(p)); p2["targets"][0]["symbol"]="9999"
    out=execute_approved_market_context_plan(p2,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),f)),execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="blocked" and out["network_operations_attempted"]==0 and f.calls==[]
    assert any(i["code"] in {"plan_hash_mismatch","plan_internal_scope_mismatch","approval_plan_hash_mismatch"} for i in out["preflight"]["issues"])

def test_expired_consumed_unapproved_and_unsafe_output_scope_fail():
    p=plan_for([stock()], sources=["TWSE_MIS"]); f=Fake(); reg=registry((("planned_network_fetch","TWSE_MIS"),f))
    for approval in [approve(p, expires_at_utc="2020-01-01T00:00:00Z"), approve(p, approval_status="consumed"), approve(p, approval_status="pending")]:
        assert execute_approved_market_context_plan(p,approval,executor_registry=reg,execution_time_utc=NOW,allow_network=True)["execution_status"]=="blocked"
    bad=json.loads(json.dumps(p)); bad["output_scope"]={"artifact_root":"../bad","write_artifacts":False,"raw_payload_retention":False}
    out=execute_approved_market_context_plan(bad,approve(p),executor_registry=reg,execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="blocked" and any(i["code"] in {"unsafe_output_scope","plan_hash_mismatch","plan_internal_scope_mismatch"} for i in out["preflight"]["issues"])

def test_unknown_executor_and_research_source_fail_closed():
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p)
    out=execute_approved_market_context_plan(p,a,executor_registry={},execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="blocked" and out["network_operations_attempted"]==0 and out["operation_results"][0]["status"]=="blocked"
    p2=json.loads(json.dumps(p)); p2["planned_source_families"]=["M9_RESEARCH"]; p2["source_to_target_context_mapping"][0]["source_family"]="M9_RESEARCH"; p2["plan_hash"]="bad"
    out2=execute_approved_market_context_plan(p2,a,executor_registry=registry(),execution_time_utc=NOW,allow_network=True)
    assert out2["execution_status"]=="blocked"

def test_one_shot_no_retry_consumes_single_use_and_reuse_blocks():
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p, single_use=True); f=Fake(status="failed"); reg=registry((("planned_network_fetch","TWSE_MIS"),f)); store=InMemoryApprovalConsumptionStore()
    out=execute_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=store)
    assert len(f.calls)==1 and out["approval_state"]["approval_status"]=="consumed"
    assert out["execution_receipt"]["one_shot"] is True and out["execution_receipt"]["auto_retry"] is False
    out2=execute_approved_market_context_plan(p,out["approval_state"],executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=store)
    assert out2["execution_status"]=="blocked" and len(f.calls)==1

def test_partial_completion_builds_m8_core_and_missing_context():
    p=plan_for([stock("2330","TWSE"), stock("6488","TPEX")], sources=["TWSE_MIS"]); a=approve(p)
    f1=Fake(); f2=Fake(status="failed")
    def router(**kw):
        return (f2 if kw["operation"]["target_id"].startswith("TPEX") else f1)(**kw)
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),router)),execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="partial" and len(out["missing_context"])==1 and out["m8_context_core"]["schema_version"]=="m8_00_multi_source_market_context.v1"

@pytest.mark.parametrize("target,source", [
    (stock("2330","TWSE"), "TWSE_MIS"), (stock("6488","TPEX"), "TWSE_MIS"), ({"market":"TWSE","instrument_type":"index","symbol":"TAIEX"}, "TWSE_MIS"),
    (stock("2330","TWSE"), "TWSE_OPENAPI"), (stock("6488","TPEX"), "TPEX_OPENAPI"), (future(), "TAIFEX_OPENAPI"),
])
def test_complete_success_operation_types(target, source):
    ctx=("official_eod_reference",) if source.endswith("OPENAPI") and source != "TAIFEX_OPENAPI" else (("official_statistical_reference",) if source=="TAIFEX_OPENAPI" else ("liveish_observation",))
    p=plan_for([target], contexts=ctx, sources=[source]); a=approve(p); f=Fake(returned_identity={"expiry":"202607","contract_type":"monthly","session":"regular"})
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch",source),f)),execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"] in {"ready","ready_with_caveats"} and len(f.calls)==1

def test_local_source_health_and_market_clock_execute_without_network():
    p=plan_for([stock()], contexts=("source_health","market_session_state"), sources=["TWSE_MIS"]); a=approve(p)
    out=execute_approved_market_context_plan(p,a,execution_time_utc=NOW,allow_network=False)
    assert out["execution_status"] in {"ready","ready_with_caveats"}
    assert out["execution_receipt"]["network_operations_attempted"]==0 and out["execution_receipt"]["local_operations_attempted"]==2

def test_taifex_exact_identity_passed_mismatch_and_unsupported_blocked_before_network():
    p=plan_for([future()], sources=["TAIFEX_MIS"]); a=approve(p); good=Fake(returned_identity={"expiry":"202607","contract_type":"monthly","session":"regular"})
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TAIFEX_MIS"),good)),execution_time_utc=NOW,allow_network=True)
    assert good.calls[0][1]["derivative_identity"]["expiry"]=="202607" and out["execution_status"] in {"ready","ready_with_caveats"}
    bad=Fake(returned_identity={"expiry":"202608","contract_type":"monthly"}); out2=execute_approved_market_context_plan(p,approve(p),executor_registry=registry((("planned_network_fetch","TAIFEX_MIS"),bad)),execution_time_utc=NOW,allow_network=True)
    assert out2["missing_context"][0]["reason_code"]=="source_identity_mismatch"
    def unsupported(**kw): raise AssertionError("must not call")
    unsupported.supports_exact_derivative_identity=False
    out3=execute_approved_market_context_plan(p,approve(p),executor_registry=registry((("planned_network_fetch","TAIFEX_MIS"),unsupported)),execution_time_utc=NOW,allow_network=True)
    assert out3["execution_status"]=="blocked" and out3["network_operations_attempted"]==0 and out3["operation_results"][0]["status"]=="blocked"

def test_option_identity_mismatch_fails_closed():
    p=plan_for([option()], sources=["TAIFEX_MIS"]); a=approve(p); f=Fake(returned_identity={"expiry":"202607","strike_price":"21000","option_type":"call"})
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TAIFEX_MIS"),f)),execution_time_utc=NOW,allow_network=True)
    assert out["missing_context"][0]["reason_code"]=="source_identity_mismatch"

def test_grouping_retention_raw_payload_absent_and_artifact_writes(tmp_path):
    p=plan_for([stock()], sources=["TWSE_MIS"], root=str(tmp_path.relative_to(Path.cwd())) if tmp_path.is_relative_to(Path.cwd()) else "research/m8r/test_artifacts")
    a=approve(p); f=Fake(); out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),f)),execution_time_utc=NOW,allow_network=True)
    text=json.dumps(out)
    assert '"raw_payload": {' not in text and out["execution_receipt"]["raw_payload_retained"] is False and out["execution_receipt"]["full_market_retained_output"] is False
    root=Path("research/m8r/test_artifacts")
    if root.exists():
        import shutil; shutil.rmtree(root)
    files=write_execution_artifacts(plan={**p,"output_scope":{"artifact_root":str(root)}}, approval=out["approval_state"], receipt=out["execution_receipt"], operation_results=out["operation_results"], missing_context=out["missing_context"], m8_context_core=out["m8_context_core"])
    assert {Path(x).name for x in files} == {"execution_plan.json","approval_record.json","execution_receipt.json","operation_results.json","missing_context.json","m8_context_core.json"}




def test_single_use_without_store_blocks_before_executor_call_and_single_use_false_allows():
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p, single_use=True); f=Fake(); reg=registry((("planned_network_fetch","TWSE_MIS"),f))
    pre=preflight_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True)
    assert pre["preflight_status"]=="blocked" and pre["issues"][0]["code"]=="approval_consumption_store_required"
    out=execute_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="blocked" and out["network_operations_attempted"]==0 and f.calls==[]
    a2=approve(p, single_use=False)
    out2=execute_approved_market_context_plan(p,a2,executor_registry=reg,execution_time_utc=NOW,allow_network=True)
    assert out2["execution_status"] in {"ready","ready_with_caveats"} and len(f.calls)==1

def test_consumption_store_blocks_original_approval_replay_and_preflight_does_not_consume(tmp_path):
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p, single_use=True); f=Fake(); store=InMemoryApprovalConsumptionStore(); reg=registry((("planned_network_fetch","TWSE_MIS"),f))
    first=execute_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=store)
    assert first["execution_status"] in {"ready","ready_with_caveats"} and len(f.calls)==1
    replay=execute_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=store)
    assert replay["execution_status"]=="blocked" and replay["network_operations_attempted"]==0 and len(f.calls)==1
    p_bad=json.loads(json.dumps(p)); p_bad["plan_hash"]="bad"
    pre=execute_approved_market_context_plan(p_bad,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=InMemoryApprovalConsumptionStore())
    assert pre["execution_status"]=="blocked"
    fresh=InMemoryApprovalConsumptionStore(); assert not fresh.is_consumed(a["approval_id"], p["plan_id"], p["plan_hash"])

def test_filesystem_consumption_store_reload_and_different_hash_same_approval_block(tmp_path):
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p, single_use=True); f=Fake(); reg=registry((("planned_network_fetch","TWSE_MIS"),f)); root=tmp_path/"ledger"
    out=execute_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=FilesystemApprovalConsumptionStore(str(root)))
    assert out["execution_status"] in {"ready","ready_with_caveats"}
    reloaded=FilesystemApprovalConsumptionStore(str(root))
    assert execute_approved_market_context_plan(p,a,executor_registry=reg,execution_time_utc=NOW,allow_network=True,approval_consumption_store=reloaded)["execution_status"]=="blocked"
    assert reloaded.is_consumed(a["approval_id"], p["plan_id"], "different_hash") is True

def test_consumption_write_failure_blocks_before_executor_calls():
    class FailingStore:
        def is_consumed(self, approval_id, plan_id, plan_hash): return False
        def consume(self, approval_id, plan_id, plan_hash, consumed_at_utc, receipt_id): raise OSError("disk full secret-token")
    p=plan_for([stock()], sources=["TWSE_MIS"]); a=approve(p, single_use=True); f=Fake()
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),f)),execution_time_utc=NOW,allow_network=True,approval_consumption_store=FailingStore())
    assert out["execution_status"]=="blocked" and out["network_operations_attempted"]==0 and f.calls==[]
    assert out["execution_receipt"]["issues"][0]["code"]=="approval_consumption_record_failed"

def test_output_scope_override_must_equal_approved_root_and_writer_not_invoked_on_mismatch(tmp_path):
    p=plan_for([stock()], sources=["TWSE_MIS"], root="research/m8r/test_artifacts"); a=approve(p); f=Fake()
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),f)),execution_time_utc=NOW,allow_network=True)
    import shutil; shutil.rmtree("research/m8r/test_artifacts", ignore_errors=True)
    files=write_execution_artifacts(plan=p, approval=out["approval_state"], receipt=out["execution_receipt"], operation_results=out["operation_results"], missing_context=out["missing_context"], m8_context_core=out["m8_context_core"])
    assert files and out["execution_receipt"]["approved_output_scope"]["artifact_root"]=="research/m8r/test_artifacts"
    with pytest.raises(OSError, match="approved_output_scope_mismatch"):
        write_execution_artifacts(plan=p, approval=out["approval_state"], receipt={**out["execution_receipt"],"receipt_id":"other"}, operation_results=[], missing_context=[], m8_context_core=None, artifact_root="research/m8r/other_safe")
    shutil.rmtree("research/m8r/test_artifacts", ignore_errors=True)

def test_executor_operational_exceptions_and_builder_failure_are_contained():
    p=plan_for([stock("2330","TWSE"), stock("6488","TPEX")], sources=["TWSE_MIS"]); a=approve(p)
    def router(**kw):
        if kw["operation"]["target_id"].startswith("TPEX"): raise TimeoutError("timeout secret-token")
        return Fake()(**kw)
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),router)),execution_time_utc=NOW,allow_network=True, m8_context_builder=lambda *a, **k: (_ for _ in ()).throw(ValueError("bad raw secret")))
    assert out["execution_status"]=="partial" and out["m8_context_core"] is None
    assert out["m8_context_core_status"]["status"]=="build_failed"
    assert any(r["issues"] and r["issues"][0]["error_class"]=="TimeoutError" for r in out["operation_results"])
    assert "secret-token" not in json.dumps(out) and "bad raw secret" not in json.dumps(out)

def test_oserror_executor_failure_contained_and_unrelated_operation_continues():
    p=plan_for([stock("2330","TWSE"), stock("6488","TPEX")], sources=["TWSE_MIS"]); a=approve(p)
    def router(**kw):
        if kw["operation"]["target_id"].startswith("TWSE"): raise OSError("socket secret")
        return Fake()(**kw)
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),router)),execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="partial"
    assert {r["status"] for r in out["operation_results"]} == {"failed","succeeded"}
    assert "socket secret" not in json.dumps(out)

def test_local_context_identity_preserves_target_market_and_stays_outside_m8_core():
    p=plan_for([stock("2330","TWSE"), stock("6488","TPEX"), future()], contexts=("source_health","market_session_state"), sources=["TWSE_MIS","TAIFEX_MIS"]); a=approve(p)
    out=execute_approved_market_context_plan(p,a,execution_time_utc=NOW,allow_network=False)
    markets={r["source_observation"]["safe_fields"].get("target_market") for r in out["operation_results"] if r["context_type"]=="market_session_state"}
    assert {"TWSE","TPEX","TAIFEX"}.issubset(markets)
    assert {r["source_observation"]["source_id"] for r in out["operation_results"]} <= {"LOCAL_SOURCE_HEALTH","LOCAL_MARKET_CLOCK"}
    assert out["m8_context_core"] is None

def test_taifex_identity_normalization_and_missing_returned_evidence_fails():
    p=plan_for([option()], sources=["TAIFEX_MIS"]); a=approve(p)
    good=Fake(returned_identity={"contract_month_or_week":"202607","strike_price":"20000.0","option_type":"CALL","contract_type":"monthly","session":"regular_session"})
    assert execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TAIFEX_MIS"),good)),execution_time_utc=NOW,allow_network=True)["execution_status"] in {"ready","ready_with_caveats"}
    for returned in [
        {"contract_month_or_week":"202608","strike_price":"20000.0","option_type":"CALL","contract_type":"monthly","session":"regular"},
        {"contract_month_or_week":"202607","strike_price":"21000","option_type":"CALL","contract_type":"monthly","session":"regular"},
        {"contract_month_or_week":"202607","strike_price":"20000","option_type":"PUT","contract_type":"monthly","session":"regular"},
        {"contract_month_or_week":"202607","strike_price":"20000","option_type":"CALL","contract_type":"weekly","session":"regular"},
        {"contract_month_or_week":"202607","strike_price":"20000","option_type":"CALL","contract_type":"monthly","session":"after_hours"},
        {"contract_month_or_week":"202607","strike_price":"20000","option_type":"CALL"},
    ]:
        out=execute_approved_market_context_plan(p,approve(p),executor_registry=registry((("planned_network_fetch","TAIFEX_MIS"),Fake(returned_identity=returned))),execution_time_utc=NOW,allow_network=True)
        assert out["missing_context"][0]["reason_code"]=="source_identity_mismatch"

def test_operation_level_blocking_allows_unrelated_operation_to_proceed():
    p=plan_for([stock(), future()], sources=["TWSE_MIS","TAIFEX_MIS"]); a=approve(p); twse=Fake()
    def unsupported(**kw): raise AssertionError("should not execute")
    unsupported.supports_exact_derivative_identity=False
    out=execute_approved_market_context_plan(p,a,executor_registry=registry((("planned_network_fetch","TWSE_MIS"),twse), (("planned_network_fetch","TAIFEX_MIS"),unsupported)),execution_time_utc=NOW,allow_network=True)
    assert out["execution_status"]=="partial" and len(twse.calls)==1
    assert any(r["status"]=="blocked" and r["source_family"]=="TAIFEX_MIS" for r in out["operation_results"])
