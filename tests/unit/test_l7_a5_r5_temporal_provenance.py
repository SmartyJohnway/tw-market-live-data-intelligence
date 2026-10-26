"""R5 acquisition and finalization chronology; memory-only source transports."""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker

from server.services import phase_i_i3_production_transport as transport
from server.services.phase_i_i3_cash_institutional_flow_production_candidate import production_batch_operation_adapter_candidate
from scripts import m8a_twse_official_eod_adapter as twse, m8a_tpex_official_eod_adapter as tpex
from tests.unit.test_phase_i_i3_a4_candidate import _request, _bytes, _telemetry, _Response

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-10-01T11:00:03Z"
FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date-time", raises=(ValueError, TypeError))
def _rfc3339_for_offline_schema_tests(value):
    # jsonschema's date-time extra is optional in the accepted local graph.
    if not isinstance(value, str): return True
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.tzinfo is not None and "T" in value



def _complete(tmp_path):
    body = _bytes("TWSE")
    production_batch_operation_adapter_candidate([_request("TWSE", "1101")], SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)),
        acquire=lambda *a, **k: transport.Acquisition(body, _telemetry("TWSE", body)))
    return json.loads(next((tmp_path / "evidence").rglob("*.json")).read_text())


@pytest.mark.parametrize("case,valid", [("complete", True), ("transport_null", True), ("fabricated_failure", False),
    ("normalization_failure", True), ("complete_null", False), ("binding", True), ("binding_incomplete", False),
    ("unavailable_incomplete", False), ("missing", False), ("invalid_datetime", False)])
@pytest.mark.parametrize("embedded", [False, True])
def test_schema_transport_condition_equivalence(tmp_path, case, valid, embedded):
    e = _complete(tmp_path)
    if case in {"transport_null", "fabricated_failure", "normalization_failure", "binding", "binding_incomplete", "unavailable_incomplete"}:
        for key in ["unit", "foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total", "institutional_total_net_shares", "source_native_optional"]:
            e.pop(key, None)
        e.update(status="binding_failed" if case.startswith("binding") else "unavailable" if case.startswith("unavailable") else "source_failed", error_code="synthetic_failure")
    if case in {"transport_null", "fabricated_failure", "binding_incomplete", "unavailable_incomplete"}:
        e["transport"].update(complete_body_received=False, response_byte_count=0, response_sha256=None)
        e["retrieved_at"] = None if case != "fabricated_failure" else STAMP
    if case == "complete_null": e["retrieved_at"] = None
    if case == "missing": e.pop("retrieved_at")
    if case == "invalid_datetime": e["retrieved_at"] = "not-a-date"
    schema = json.loads((ROOT / "schemas" / ("unified_market_evidence_result.v3.schema.json" if embedded else "cash_institutional_flow_context_evidence.v2.schema.json")).read_text())
    if embedded: schema = {**schema, "$ref": "#/definitions/cash_institutional_flow_context"}
    validator = (Draft7Validator if embedded else Draft202012Validator)(schema, format_checker=FORMAT_CHECKER)
    assert (not list(validator.iter_errors(e))) == valid


def test_i3_clock_after_complete_validated_body():
    events = []
    class Response(_Response):
        def read(self, n):
            value = super().read(n)
            if not value: events.append("body_complete")
            return value
    class Opener:
        def open(self, *a, **k): events.append("dispatch"); return Response(b"{}", content_length=2)
    def clock():
        assert events == ["dispatch", "body_complete"]
        events.append("retrieval_clock")
        return datetime(2026, 10, 1, 11, 0, 1, tzinfo=timezone.utc)
    acquired = transport.acquire_once("TPEX", opener=Opener(), clock=clock)
    assert events == ["dispatch", "body_complete", "retrieval_clock"]
    assert acquired.telemetry["retrieved_at"] == "2026-10-01T11:00:01Z"


def test_i3_failed_acquisition_emits_null_typed_evidence(tmp_path):
    from urllib.error import URLError
    class Opener:
        def open(self, *a, **k): raise URLError("offline failure")
    def acquire(*a, **k):
        return transport.acquire_once("TPEX", opener=Opener(), clock=lambda: pytest.fail("failed retrieval must not sample completion clock"))
    result = production_batch_operation_adapter_candidate([_request("TPEX", "5347")], SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)), acquire=acquire)
    e = json.loads(next((tmp_path / "evidence").rglob("*.json")).read_text())
    assert result[0]["status"] == "failed" and e["status"] == "source_failed"
    assert e["retrieved_at"] is None and e["transport"]["complete_body_received"] is False
    assert e["transport"]["failure_phase"] == "connection" and e["transport"]["error_code"] == "URLError"


def test_i3_normalization_failure_retains_completed_retrieval(tmp_path):
    class Opener:
        def open(self, *a, **k): return _Response(b"{}")
    def acquire(*a, **k): return transport.acquire_once("TWSE", resolved_source_trade_date="2026-09-30", opener=Opener(), clock=lambda: datetime(2026,10,1,11,0,1,tzinfo=timezone.utc))
    out = production_batch_operation_adapter_candidate([_request("TWSE", "1101")], SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)), acquire=acquire)
    e = json.loads(next((tmp_path / "evidence").rglob("*.json")).read_text())
    assert e["status"] == "source_failed" and e["transport"]["complete_body_received"] is True
    assert e["retrieved_at"] == "2026-10-01T11:00:01Z"
    assert "source preparation failed: twse_root_invalid" in e["caveats"]
    assert "source preparation failed: twse_root_invalid" in out[0]["warnings"]


@pytest.mark.parametrize("module,prefix", [(twse,"twse"),(tpex,"tpex")])
def test_eod_fetch_retrieval_parse_completion_order(monkeypatch, module, prefix):
    events=[]
    rows=json.loads((ROOT/"tests/fixtures/m8a_official_eod"/(prefix+"_normal_rows.json")).read_text())
    def fetch(**k): events.append("fetch_complete"); return rows,200,"application/json"
    original=getattr(module,"parse_"+prefix+"_official_eod_rows")
    def parse(*a,**k): events.append("parse"); return original(*a,**k)
    def clock():
        events.append("retrieval_clock" if events == ["fetch_complete"] else "completion_clock")
        return "2026-10-01T11:00:01Z" if events[-1]=="retrieval_clock" else "2026-10-01T11:00:02Z"
    monkeypatch.setattr(module,"fetch_"+prefix+"_official_eod_json",fetch)
    monkeypatch.setattr(module,"parse_"+prefix+"_official_eod_rows",parse)
    monkeypatch.setattr(module,"utc_now",clock)
    result=getattr(module,"execute_"+prefix+"_official_eod_adapter")(["2330" if prefix=="twse" else "8069"],security_master={})
    assert events==["fetch_complete","retrieval_clock","parse","completion_clock"]
    assert result["observations"][0]["retrieved_at_utc"] <= result["completed_at_utc"]
    assert result["requested_at_utc"]=="2026-10-01T11:00:01Z"


@pytest.mark.parametrize("module,prefix",[(twse,"twse"),(tpex,"tpex")])
def test_eod_fetch_failure_no_successful_observation(monkeypatch,module,prefix):
    def fail(**k):raise OSError("offline failure")
    monkeypatch.setattr(module,"fetch_"+prefix+"_official_eod_json",fail)
    result=getattr(module,"execute_"+prefix+"_official_eod_adapter")(["2330"],security_master={})
    assert result["source_status"]=="error" and result["observations"]==[]


@pytest.mark.parametrize("failed",[False,True])
@pytest.mark.parametrize("official_cli",[False,True])
def test_deferred_high_level_and_execute_once_mode_c(tmp_path,monkeypatch,failed,official_cli):
    from tests.unit.test_phase_i_i3_a4_activation import _preview,_prepared,_source
    from scripts.m8r_05b_03 import orchestrator,controlled_dispatch
    from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry,load_production_executor_metadata
    from scripts import m8r_06_03_execute_once as cli
    from scripts.m8r_05c.artifact_loader import load_projection_inputs
    from scripts.m8r_05c.result_builder import build_result
    from scripts.m8r_05c.audit_package_builder import build_audit_package
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.citation_builder import build_citation_index
    from scripts.m8r_05c.canonical import hash_body_excluding_key
    from server.services.unified_mode_b2 import _write_control_package
    _,_,package=_preview([{"input":"1101","market_hint":"TWSE"}],request_id="r5-temporal")
    prepared=_prepared(package);plan=prepared["plan"];auth=prepared["authorization"];binding=prepared["consumption_binding"];unused={"authorization_id":auth["authorization_id"],"authorization_hash":auth["authorization_hash"],"consumption_binding_id":binding["consumption_binding_id"],"consumption_binding_hash":binding["consumption_binding_hash"],"registry_contract_version":"m8r_05b_03.v1","state":"unused"}
    metadata=load_production_executor_metadata();claim_time="2026-10-01T11:00:00Z";events=[]
    preflight=build_orchestrator_preflight(plan,auth,binding,supplied_consumption_state=unused,evaluation_timestamp=claim_time,executor_registry_metadata=metadata,output_root=str(tmp_path))
    atomic=controlled_dispatch.atomic_claim_authorization
    def claim(*a,**k):events.append("claim");return atomic(*a,**k)
    monkeypatch.setattr(controlled_dispatch,"atomic_claim_authorization",claim)
    def acquire(market,**k):
        events.append("dispatch")
        if failed:
            tele=_telemetry("TWSE",b"{}");tele.update(complete_body_received=False,retrieved_at=None,response_sha256=None,response_byte_count=0,failure_phase="connection",error_code="URLError");events.append("adapter_complete");raise transport.AcquisitionError("transport_error",tele)
        body=_source(market);tele=_telemetry(market,body);tele["retrieved_at"]="2026-10-01T11:00:01Z";events.append("adapter_complete");return transport.Acquisition(body,tele)
    registry=build_production_runtime_adapter_registry(i3_acquire=acquire)
    aggregate=orchestrator.aggregate_dispatch_outcomes
    def aggregation(*a,**k):out=aggregate(*a,**k);events.append("aggregation_complete");return out
    monkeypatch.setattr(orchestrator,"aggregate_dispatch_outcomes",aggregation)
    def clock():
        assert events==["claim","dispatch","adapter_complete","aggregation_complete"]
        events.append("finalization_clock");return STAMP
    finalizer=orchestrator.finalize_consumption_and_write_receipt
    def finalize(*a,**k):assert events[-1]=="finalization_clock";events.append("finalizer");return finalizer(*a,**k)
    monkeypatch.setattr(orchestrator,"finalize_consumption_and_write_receipt",finalize)
    artifacts={"request":package["_request"],"plan":plan,"authorization":auth,"consumption_binding":binding,"unused_consumption_state":unused,"preflight":preflight}
    _write_control_package(tmp_path,artifacts)
    (tmp_path/"f3_validation.json").write_text(json.dumps(package["_validation"]),encoding="utf-8")
    if official_cli:
        monkeypatch.setattr(cli,"_configure_transport_mode",lambda:("deterministic_test_transport",False))
        monkeypatch.setattr(cli,"load_control_package",lambda _: (tmp_path,artifacts,{}))
        monkeypatch.setattr(cli,"_now",lambda:claim_time)
        monkeypatch.setattr(cli,"load_production_executor_metadata",lambda:metadata)
        monkeypatch.setattr(cli,"build_production_runtime_adapter_registry",lambda:registry)
        monkeypatch.setattr(orchestrator,"_finalization_timestamp",clock)
        cli.execute_once(auth["authorization_id"],confirm_execution=True,operator_confirmation_reference="R5_OFFLINE",confirm_network_execution=True)
    else:
        orchestrator.execute_controlled_plan(plan,auth,binding,supplied_consumption_state=unused,accepted_preflight=preflight,evaluation_timestamp=claim_time,claim_created_at=claim_time,finalization_clock=clock,executor_registry_metadata=metadata,runtime_adapter_registry=registry,output_root=str(tmp_path),mode="execute-approved",confirm_execution=True,operator_confirmation_reference="R5_OFFLINE",confirm_network_execution=True)
    claim_obj=json.loads(next((tmp_path/"claims").glob("*.json")).read_text());receipt=json.loads(next((tmp_path/"receipts").glob("*.json")).read_text());bundle=json.loads(next((tmp_path/"bundles").glob("*.json")).read_text())
    assert claim_obj["claim_created_at"]==claim_time
    assert claim_obj["finalized_at"]==receipt["finalized_at"]==bundle["finalized_at"]==STAMP
    inputs=load_projection_inputs(request_path=str(tmp_path/"control/request.json"),f3_validation_path=str(tmp_path/"f3_validation.json"),plan_path=str(tmp_path/"control/plan.json"),authorization_path=str(tmp_path/"control/authorization.json"),consumption_binding_path=str(tmp_path/"control/consumption_binding.json"),claim_path=str(next((tmp_path/"claims").glob("*.json"))),receipt_path=str(next((tmp_path/"receipts").glob("*.json"))),bundle_path=str(next((tmp_path/"bundles").glob("*.json"))),artifact_root=str(tmp_path),calculated_at=receipt["finalized_at"],calculated_at_source="receipt.finalized_at")
    result=build_result(inputs,output_schema_version="unified_market_evidence_result.v3")
    citations=build_citation_index(build_lineage_map(inputs),inputs.bundle,"unified_market_evidence_result.v3")
    audit=build_audit_package(result,inputs,citations,"result.v3.json",output_schema_version="unified_market_evidence_audit_package.v3")
    assert result["generated_at"]==STAMP and hash_body_excluding_key(result,"result_hash")==result["result_hash"]
    Draft7Validator(json.loads((ROOT/"schemas/unified_market_evidence_result.v3.schema.json").read_text()),format_checker=FORMAT_CHECKER).validate(result)
    Draft7Validator(json.loads((ROOT/"schemas/unified_market_evidence_audit_package.v3.schema.json").read_text()),format_checker=FORMAT_CHECKER).validate(audit)
    if failed:assert '"retrieved_at": null' in json.dumps(result)

@pytest.mark.parametrize("complete,value,error", [(True,None,"timestamp_missing"),(False,STAMP,"timestamp_forbidden")])
def test_i3_consumer_rejects_transport_timestamp_mismatch(tmp_path,complete,value,error):
    body=_bytes("TWSE");tele=_telemetry("TWSE",body);tele.update(complete_body_received=complete,retrieved_at=value)
    with pytest.raises(Exception,match=error):
        production_batch_operation_adapter_candidate([_request("TWSE","1101")],SimpleNamespace(mode="execute-approved",governed_output_root=str(tmp_path)),acquire=lambda *a,**k:transport.Acquisition(body,tele))
    assert not list(tmp_path.rglob("*.json"))


def test_high_level_rejects_precomputed_finalized_at():
    from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
    with pytest.raises(TypeError,match="finalized_at"):
        execute_controlled_plan({}, {}, {},finalized_at=STAMP)
