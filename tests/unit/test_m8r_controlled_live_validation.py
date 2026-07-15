import argparse, json
from pathlib import Path

import pytest

from scripts import run_m8r_controlled_live_validation as live
from scripts.m8r_one_shot_market_context_orchestrator import FilesystemApprovalConsumptionStore, execute_approved_market_context_plan
from scripts.m8r_bounded_market_context_request import build_approval_artifact


def args(**kw):
    base=dict(operator_confirmed=False, allow_network=False, dry_run=True, artifact_root="research/m8r/live_validation/test", execution_time_utc="2026-07-15T00:00:00Z", taifex_future_product=None, taifex_future_expiry=None, taifex_option_product=None, taifex_option_underlying=None, taifex_option_expiry=None, taifex_option_strike=None, taifex_option_call_put=None)
    base.update(kw)
    return argparse.Namespace(**base)


def test_case_definitions_and_manifest(tmp_path, monkeypatch):
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


def test_builds_single_use_approval_and_requires_store(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    a=args(artifact_root=str(tmp_path.relative_to(Path.cwd())) if tmp_path.is_relative_to(Path.cwd()) else "research/m8r/live_validation/unit")
    p=live.plan_for("TWSE_MIS_LISTED_2330",live.CASES["TWSE_MIS_LISTED_2330"],a,"research/m8r/live_validation/unit")
    appr=build_approval_artifact(p, approved_at_utc=a.execution_time_utc, single_use=True)
    out=execute_approved_market_context_plan(p,appr,allow_network=False,execution_time_utc=a.execution_time_utc,approval_consumption_store=None)
    assert out["preflight"]["network_operations_attempted"]==0
    assert out["missing_context"][0]["reason_code"] in {"approval_consumption_store_required","network_execution_not_enabled"}


def test_raw_key_audit_detects_marker(tmp_path):
    root=tmp_path/"audit"; root.mkdir(); (root/"x.json").write_text(json.dumps({"raw_payload": {}}))
    out=live.audit(root)
    assert out["status"]=="failed" and out["forbidden_key_hits"][0]["key"]=="raw_payload"


def test_acceptance_decision_readiness_flags(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    res=[{"case_id":"A","planned_source_family":f,"result":"passed","retention_audit":{"status":"passed"},"ai_package_status":"ready"} for f in ["TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI"]]
    s=live.summary("research/m8r/live_validation/run", args(), res)
    assert s["decision"]=="GO"
    assert s["production_live_execution_ready"] is True
    res[0]["result"]="source_temporarily_unavailable"
    s=live.summary("research/m8r/live_validation/run", args(), res)
    assert s["decision"]=="CONDITIONAL_GO"
    assert s["production_live_execution_ready"] is False


def test_dry_run_does_not_consume_approval(monkeypatch):
    monkeypatch.setattr(live, "git_sha", lambda: "abc")
    out=live.run_case("TWSE_MIS_LISTED_2330", args(), "research/m8r/live_validation/dry-unit")
    assert out["dry_run"] is True
    assert out["preflight"]["network_operations_attempted"]==0
    assert out["preflight"]["preflight_status"]=="blocked"
