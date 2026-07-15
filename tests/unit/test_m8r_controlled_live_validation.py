import argparse, json
from pathlib import Path

import pytest

from scripts import run_m8r_controlled_live_validation as live
from scripts.m8r_one_shot_market_context_orchestrator import execute_approved_market_context_plan
from scripts.m8r_bounded_market_context_request import build_approval_artifact


def args(**kw):
    base=dict(operator_confirmed=False, allow_network=False, dry_run=True, run_negative_controls=False, artifact_root="research/m8r/live_validation/test", execution_time_utc="2026-07-15T00:00:00Z", taifex_future_product=None, taifex_future_expiry=None, taifex_option_product=None, taifex_option_underlying=None, taifex_option_expiry=None, taifex_option_strike=None, taifex_option_call_put=None)
    base.update(kw)
    return argparse.Namespace(**base)


def case(cid, source="TWSE_MIS", result="passed", ai_status="ready", valid=True, written=True):
    return {"case_id":cid,"planned_source_family":source,"result":result,"retention_audit":{"status":"passed"},"ai_package_status":ai_status,"ai_validation":{"valid":valid,"reason_code":None if valid else "ai_package_build_failed"},"ai_artifacts_written":written,"approval_consumed":True,"operation_status":"succeeded","network_request_count":1}


def all_pass_cases():
    return [
        case("TWSE_MIS_LISTED_2330","TWSE_MIS"), case("TWSE_MIS_OTC_6488","TWSE_MIS"), case("TWSE_MIS_TAIEX","TWSE_MIS"),
        case("TWSE_OPENAPI_EOD_2330","TWSE_OPENAPI"), case("TPEX_OPENAPI_EOD_6488","TPEX_OPENAPI"),
        case("TAIFEX_MIS_FUTURE_EXACT","TAIFEX_MIS"), case("TAIFEX_MIS_OPTION_EXACT","TAIFEX_MIS"),
        case("TAIFEX_OPENAPI_FUTURE_EXACT","TAIFEX_OPENAPI"), case("TAIFEX_OPENAPI_OPTION_EXACT","TAIFEX_OPENAPI"),
    ]


def controls(**overrides):
    base={k:{"passed":True} for k in ["NETWORK_DISABLED","MISSING_CONSUMPTION_STORE","APPROVAL_REPLAY","MODIFIED_PLAN_AFTER_APPROVAL","UNSUPPORTED_TAIFEX_IDENTITY"]}
    base.update(overrides); return base


def test_case_definitions_and_manifest(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    root="research/m8r/live_validation/unit"
    m=live.manifest(root,args(),["TWSE_MIS_LISTED_2330"])
    assert m["schema_version"]==live.MANIFEST_SCHEMA_VERSION
    assert m["required_cases"]==["TWSE_MIS_LISTED_2330"]
    assert live.CASES["TAIFEX_MIS_FUTURE_EXACT"]["taifex"]=="future"


def test_artifact_root_rejects_absolute_traversal_and_forbidden():
    for bad in ["/tmp/x","../x","research/generated/x","frontend/public/x"]:
        with pytest.raises(SystemExit): live.safe_root(bad)
    assert live.safe_root("research/m8r/live_validation/x").endswith("x")


def test_taifex_parameters_mandatory_no_defaults():
    with pytest.raises(SystemExit): live.target_for(live.CASES["TAIFEX_MIS_FUTURE_EXACT"], args())
    with pytest.raises(SystemExit): live.target_for(live.CASES["TAIFEX_MIS_OPTION_EXACT"], args(taifex_option_product="TXO"))
    t=live.target_for(live.CASES["TAIFEX_MIS_FUTURE_EXACT"], args(taifex_future_product="TX", taifex_future_expiry="202607"))
    assert t["expiry"]=="202607" and t["contract_type"]=="monthly" and t["session"]=="regular"


def test_builds_single_use_approval_and_requires_store(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    a=args()
    p=live.plan_for("TWSE_MIS_LISTED_2330",live.CASES["TWSE_MIS_LISTED_2330"],a,"research/m8r/live_validation/unit")
    appr=build_approval_artifact(p, approved_at_utc=a.execution_time_utc, single_use=True)
    out=execute_approved_market_context_plan(p,appr,allow_network=False,execution_time_utc=a.execution_time_utc,approval_consumption_store=None)
    assert out["preflight"]["network_operations_attempted"]==0
    assert out["missing_context"][0]["reason_code"] in {"approval_consumption_store_required","network_execution_not_enabled"}


def test_raw_key_audit_detects_marker(tmp_path):
    root=tmp_path/"audit"; root.mkdir(); (root/"x.json").write_text(json.dumps({"raw_payload": {}}))
    out=live.audit(root)
    assert out["status"]=="failed" and out["forbidden_key_hits"][0]["key"]=="raw_payload"


@pytest.mark.parametrize("reason", ["ai_package_build_failed", "ai_package_validation_failed", "ai_package_artifact_write_failed"])
def test_execution_success_ai_failures_do_not_pass(reason):
    result={"execution_status":"ready_with_caveats","operation_results":[{"status":"succeeded","issues":[]}]}
    ai={"ai_package_id":None if reason=="ai_package_build_failed" else "amc-x", "ai_package_status":"build_failed", "ai_validation":{"valid":False,"reason_code":reason}, "ai_artifacts_written":False}
    assert live.classify(result, ai, {"status":"passed"}) == "failed_runtime_contract"


def test_placeholder_package_cannot_pass():
    result={"execution_status":"ready","operation_results":[{"status":"succeeded","issues":[]}]}
    placeholder={"ai_package":{"schema_version":"ai_market_context.v1"},"ai_package_id":None,"ai_package_status":"ready","ai_validation":{"valid":True},"ai_artifacts_written":True}
    assert live.classify(result, placeholder, {"status":"passed"}) == "failed_runtime_contract"


def test_summary_preserves_multiple_cases_per_source_and_go_requires_all(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    s=live.summary("research/m8r/live_validation/run", args(), all_pass_cases(), controls())
    assert s["decision"]=="GO"
    assert set(s["source_family_results"]["TWSE_MIS"]) == {"TWSE_MIS_LISTED_2330","TWSE_MIS_OTC_6488","TWSE_MIS_TAIEX"}
    assert s["exact_future_acceptance"]["accepted"] is True and s["exact_option_acceptance"]["accepted"] is True
    missing=all_pass_cases()[:-1]
    assert live.summary("research/m8r/live_validation/run", args(), missing, controls())["decision"]=="NO_GO"
    no_option=[c for c in all_pass_cases() if not c["case_id"].endswith("OPTION_EXACT")]
    assert live.summary("research/m8r/live_validation/run", args(), no_option, controls())["decision"]=="NO_GO"


def test_runtime_critical_fails_when_replay_or_ai_writer_evidence_absent(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    bad_controls=controls(APPROVAL_REPLAY={"passed":False})
    s=live.summary("research/m8r/live_validation/run", args(), all_pass_cases(), bad_controls)
    assert s["runtime_critical_status"]=="failed" and s["decision"]=="NO_GO"
    bad_cases=all_pass_cases(); bad_cases[0]["ai_artifacts_written"]=False
    s=live.summary("research/m8r/live_validation/run", args(), bad_cases, controls())
    assert s["runtime_critical_status"]=="failed"


def test_conditional_go_only_for_allowed_temporary_source_condition(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    temp=all_pass_cases(); temp[0]["result"]="source_temporarily_unavailable"
    assert live.summary("research/m8r/live_validation/run", args(), temp, controls())["decision"]=="CONDITIONAL_GO"
    generic=all_pass_cases(); generic[0]["result"]="failed_runtime_contract"
    assert live.summary("research/m8r/live_validation/run", args(), generic, controls())["decision"]=="NO_GO"


def test_negative_controls_execute_and_write_results(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    root="research/m8r/live_validation/unit-controls"
    import shutil; shutil.rmtree(root, ignore_errors=True)
    out=live.run_negative_controls(args(execution_time_utc="2026-07-15T00:00:00Z"), root)
    assert {"NETWORK_DISABLED","MISSING_CONSUMPTION_STORE","APPROVAL_REPLAY","MODIFIED_PLAN_AFTER_APPROVAL","UNSUPPORTED_TAIFEX_IDENTITY"} <= set(out)
    assert out["APPROVAL_REPLAY"]["passed"] is True
    assert out["APPROVAL_REPLAY"]["network_operations_attempted"] == 0
    assert out["APPROVAL_REPLAY"]["adapter_invocation_count"] == 0
    assert Path(root,"controls","APPROVAL_REPLAY","control_result.json").exists()


def test_dry_run_does_not_consume_approval(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    out=live.run_case("TWSE_MIS_LISTED_2330", args(), "research/m8r/live_validation/dry-unit")
    assert out["dry_run"] is True
    assert out["preflight"]["network_operations_attempted"]==0
    assert out["preflight"]["preflight_status"]=="blocked"


def test_manual_ai_artifact_fallback_absent():
    text=Path("scripts/run_m8r_controlled_live_validation.py").read_text()
    assert "except FileExistsError" not in text
    assert "ai_market_context_v1.json" not in text
