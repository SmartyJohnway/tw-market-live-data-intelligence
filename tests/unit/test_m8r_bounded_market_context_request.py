import ast
import json
from pathlib import Path

import pytest

from scripts import m8r_bounded_market_context_request as m8r

BASE = {
    "schema_version": m8r.REQUEST_SCHEMA_VERSION,
    "request_id": "case-1",
    "requested_context_types": ["liveish_observation", "official_eod_reference"],
    "targets": [{"symbol": "2330", "market": "TWSE", "instrument_type": "equity"}],
    "output_policy": {"artifact_root": "research/m8r/planned/case-1"},
}

def plan(req=BASE, **kw):
    r = json.loads(json.dumps(req)); r.update(kw)
    return m8r.compile_market_context_execution_plan(r, created_at_utc="2026-07-14T00:00:00Z")

def codes(result):
    return {i["code"] for i in result["issues"]}

def test_valid_twse_tpex_taiex_taifex_future_and_mixed_plan():
    req = dict(BASE, targets=[
        {"symbol":"2330","market":"TWSE","instrument_type":"equity"},
        {"symbol":"6488","market":"TPEX","instrument_type":"equity"},
        {"symbol":"TAIEX","market":"TWSE","instrument_type":"index","requested_context_types":["liveish_observation"]},
        {"symbol":"TX","market":"TAIFEX","instrument_type":"future","requested_context_types":["liveish_observation","official_statistical_reference"],"session":"regular"},
    ])
    p=plan(req)
    assert p["plan_id"].startswith("m8r-plan-")
    assert p["network_required"] is True and p["approval_required"] is True
    assert "TPEX_OPENAPI" in p["planned_source_families"]
    assert any(m["route"] == "otc_6488.tw" for m in p["source_to_target_context_mapping"])
    assert any(t["target_id"] == "TWSE:index:TAIEX" for t in p["targets"])
    assert not p["non_goal_flags"]["m9_ingestion"]

def test_valid_monthly_option_requires_exact_identity():
    req=dict(BASE, targets=[{"symbol":"TXO","market":"TAIFEX","instrument_type":"option","underlying":"TX","expiry":"202607","strike":"20000","call_put":"C","contract_type":"monthly","requested_context_types":["official_statistical_reference"]}])
    assert plan(req)["targets"][0]["identity_resolution_status"] == "resolved"

def test_explicit_source_selection_and_default_sources():
    req=dict(BASE, requested_source_families=["TWSE_MIS","TWSE_OPENAPI"])
    p=plan(req)
    assert p["planned_source_families"] == ["TWSE_MIS", "TWSE_OPENAPI"]
    assert "TAIFEX_MIS" in m8r.accepted_source_families()

def test_deterministic_normalization_hash_order_and_metadata_timestamp_exclusions():
    a=dict(BASE, targets=[{"symbol":"6488","market":"otc","instrument_type":"stock","display_name":"A"},{"symbol":"2330","market":"twse","instrument_type":"listed_equity"}])
    b=dict(BASE, targets=list(reversed(a["targets"])), requested_context_types=list(reversed(BASE["requested_context_types"])))
    pa=plan(a, request_id="same"); pb=plan(b, request_id="same")
    assert pa["plan_hash"] == pb["plan_hash"]
    pc=m8r.compile_market_context_execution_plan(dict(a, request_id="same"), created_at_utc="2030-01-01T00:00:00Z")
    assert pa["plan_hash"] == pc["plan_hash"]

def test_scope_changes_change_hash():
    base=plan()
    assert base["plan_hash"] != plan(dict(BASE, targets=[{"symbol":"0050","market":"TWSE","instrument_type":"etf"}]))["plan_hash"]
    assert base["plan_hash"] != plan(dict(BASE, requested_context_types=["liveish_observation"], requested_source_families=["TWSE_MIS"]))["plan_hash"]
    assert base["plan_hash"] != plan(dict(BASE, requested_context_types=["liveish_observation"]))["plan_hash"]
    assert base["plan_hash"] != plan(dict(BASE, output_policy={"artifact_root":"research/m8r/planned/other"}))["plan_hash"]
    mutated=json.loads(json.dumps(base)); mutated["hash_scope"]["non_goal_flags"]["polling"] = True
    assert m8r.compute_plan_hash(mutated) == base["plan_hash"]
    assert any(i["code"] == "plan_internal_scope_mismatch" for i in m8r.validate_plan_internal_consistency(mutated)["issues"])

@pytest.mark.parametrize("target,expected", [
    ({"symbol":"2330","market":"TPEX","instrument_type":"equity","requested_source_families":["TWSE_OPENAPI"]}, "source_target_incompatible"),
    ({"symbol":"6488","market":"TWSE","instrument_type":"equity","requested_source_families":["TPEX_OPENAPI"]}, "source_target_incompatible"),
    ({"symbol":"TX","market":"TWSE","instrument_type":"future"}, "instrument_type_market_incompatible"),
    ({"symbol":"TAIEX","market":"TPEX","instrument_type":"index"}, "market_symbol_incompatible"),
    ({"symbol":"2330","market":"TWSE","instrument_type":"index"}, "unresolved_identity"),
    ({"symbol":"TX","market":"TAIFEX","instrument_type":"future","requested_source_families":["TWSE_MIS"]}, "source_target_incompatible"),
    ({"symbol":"2330","market":"TWSE","instrument_type":"equity","requested_source_families":["TAIFEX_MIS"]}, "source_target_incompatible"),
    ({"symbol":"TXO","market":"TAIFEX","instrument_type":"option"}, "ambiguous_identity"),
    ({"symbol":"TXO","market":"TAIFEX","instrument_type":"option","underlying":"TX","expiry":"202607W1","strike":"20000","call_put":"P","contract_type":"weekly"}, "unsupported_product_scope"),
    ({"symbol":"TX","market":"TAIFEX","instrument_type":"future","session":"after_hours"}, "unsupported_session_scope"),
])
def test_invalid_identity_target_rejections(target, expected):
    req=dict(BASE, targets=[target])
    n=m8r.normalize_market_context_request(req)
    assert expected in {i["code"] for t in n["rejected_targets"] for i in t["issues"]}
    with pytest.raises(m8r.M8RValidationError):
        m8r.compile_market_context_execution_plan(n)

@pytest.mark.parametrize("sources,expected", [
    (["TPEX_MIS"], "unsupported_source_family"),
    (["ROTC_MIS"], "unsupported_source_family"),
    (["M9_PROVIDER"], "unsupported_source_family"),
    (["CREDENTIAL_GATED_PROVIDER"], "credential_gated_source_forbidden"),
    (["EXTERNAL_VALIDATION_ONLY"], "source_not_runtime_eligible"),
    (["MOPS"], "source_not_runtime_eligible"),
])
def test_forbidden_sources_block_request(sources, expected):
    r=dict(BASE, requested_source_families=sources)
    assert expected in codes(m8r.validate_market_context_request(r))

def test_source_with_ai_context_false_runtime_false_custom_registry():
    reg={"sources":[{"source_family":"BAD","runtime_available":True,"runtime_executable":False,"ai_context_allowed":False,"credential_required":False}]}
    r=dict(BASE, requested_source_families=["BAD"])
    assert "source_not_runtime_eligible" in codes(m8r.validate_market_context_request(r, source_registry=reg))

def test_limits_duplicates_and_unsafe_output_scope():
    too_many=dict(BASE, targets=[{"symbol":str(1000+i),"market":"TWSE","instrument_type":"equity"} for i in range(m8r.MAX_TARGETS+1)])
    assert "target_limit_exceeded" in codes(m8r.validate_market_context_request(too_many))
    bad_context=dict(BASE, requested_context_types=["liveish_observation","official_eod_reference","source_health","market_session_state","official_statistical_reference","technical_signal"])
    assert "context_limit_exceeded" in codes(m8r.validate_market_context_request(bad_context))
    bad_sources=dict(BASE, requested_source_families=["TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI","EXTERNAL_VALIDATION_ONLY"])
    assert "source_limit_exceeded" in codes(m8r.validate_market_context_request(bad_sources))
    dup=dict(BASE, targets=[{"symbol":"2330","market":"TWSE","instrument_type":"equity"},{"symbol":"2330","market":"TWSE","instrument_type":"stock","notes":"different"}])
    n=m8r.normalize_market_context_request(dup)
    assert any(i["code"]=="duplicate_target_conflict" for t in n["rejected_targets"] for i in t["issues"])
    unsafe=dict(BASE, output_policy={"artifact_root":"../frontend/public"})
    assert "unsafe_output_scope" in codes(m8r.validate_market_context_request(unsafe))
    long_id=dict(BASE, request_id="x"*(m8r.MAX_IDENTIFIER_LENGTH+1))
    assert "identifier_too_long" in codes(m8r.validate_market_context_request(long_id))

def test_unknown_context_blocks_request():
    assert "unsupported_context_type" in codes(m8r.validate_market_context_request(dict(BASE, requested_context_types=["ETF_flow"])))


def test_request_allowlist_filters_effective_sources_per_target():
    req=dict(BASE, requested_source_families=["TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI"], targets=[
        {"symbol":"2330","market":"TWSE","instrument_type":"equity"},
        {"symbol":"6488","market":"TPEX","instrument_type":"equity"},
        {"symbol":"TX","market":"TAIFEX","instrument_type":"future","requested_context_types":["liveish_observation","official_statistical_reference"]},
    ])
    p=plan(req)
    by_target={t["target_id"]: set(t["requested_source_families"]) for t in p["targets"]}
    assert by_target["TWSE:equity:2330"] == {"TWSE_MIS","TWSE_OPENAPI"}
    assert by_target["TPEX:equity:6488"] == {"TWSE_MIS","TPEX_OPENAPI"}
    assert by_target["TAIFEX:future:TX"] == {"TAIFEX_MIS","TAIFEX_OPENAPI"}
    assert not any(m.get("source_family") == "TAIFEX_MIS" and m["target_id"].startswith("TWSE:") for m in p["source_to_target_context_mapping"])

@pytest.mark.parametrize("target", [
    {"symbol":"2330","market":"TWSE","instrument_type":"equity","requested_source_families":["TWSE_MIS","TWSE_OPENAPI","TAIFEX_MIS"]},
    {"symbol":"6488","market":"TPEX","instrument_type":"equity","requested_source_families":["TWSE_MIS","TPEX_OPENAPI","TWSE_OPENAPI"]},
    {"symbol":"TX","market":"TAIFEX","instrument_type":"future","requested_context_types":["liveish_observation","official_statistical_reference"],"requested_source_families":["TAIFEX_MIS","TAIFEX_OPENAPI","TWSE_MIS"]},
])
def test_target_level_extra_incompatible_sources_reject(target):
    n=m8r.normalize_market_context_request(dict(BASE, targets=[target]))
    assert any(i["code"] == "source_target_incompatible" for t in n["rejected_targets"] for i in t["issues"])

@pytest.mark.parametrize("contexts, expected_network, classes", [
    (["source_health"], False, {"local_source_health_read"}),
    (["market_session_state"], False, {"local_market_clock_evaluation"}),
    (["source_health","market_session_state"], False, {"local_source_health_read","local_market_clock_evaluation"}),
    (["liveish_observation","source_health","market_session_state"], True, {"planned_network_fetch","local_source_health_read","local_market_clock_evaluation"}),
])
def test_local_context_planning_network_derivation(contexts, expected_network, classes):
    p=plan(dict(BASE, requested_context_types=contexts))
    assert p["network_required"] is expected_network
    assert set(p["network_scope"]["operation_classes"]) == classes
    assert p["approval_required"] is True
    for c in contexts:
        assert any(m["context_type"] == c for m in p["source_to_target_context_mapping"])


def test_plan_hash_rebuilt_from_top_level_fields_for_approval_validation():
    p=plan(); approval=m8r.build_approval_artifact(p, approved_at_utc="2026-07-14T00:00:00Z")
    mutations=[]
    for field, value in [
        ("targets", []),
        ("planned_source_families", ["TWSE_MIS"]),
        ("source_to_target_context_mapping", []),
        ("output_scope", {"artifact_root":"research/m8r/planned/tampered","write_artifacts":False,"raw_payload_retention":False}),
        ("bounded_retained_scope", {"bounded_targets_only":False,"full_market_retained_output":False,"raw_payload_retention":False}),
        ("approval_required", False),
    ]:
        m=json.loads(json.dumps(p)); m[field]=value; mutations.append(m)
    m=json.loads(json.dumps(p)); m["non_goal_flags"]["polling"] = True; mutations.append(m)
    for m in mutations:
        result=m8r.validate_approval_for_plan(approval, m, now_utc="2026-07-14T00:00:00Z")
        assert not result["valid"]
        assert {i["code"] for i in result["issues"]} & {"approval_plan_hash_mismatch","plan_hash_mismatch","plan_internal_scope_mismatch"}
    bad_hash=json.loads(json.dumps(p)); bad_hash["plan_hash"]="0"*64
    assert "plan_hash_mismatch" in {i["code"] for i in m8r.validate_approval_for_plan(approval,bad_hash)["issues"]}
    bad_scope=json.loads(json.dumps(p)); bad_scope["hash_scope"]["approval_required"] = False
    assert "plan_internal_scope_mismatch" in {i["code"] for i in m8r.validate_approval_for_plan(approval,bad_scope)["issues"]}

@pytest.mark.parametrize("expires, now, valid, expected", [
    ("not-a-time", "2026-07-14T00:00:00Z", False, "invalid_approval_timestamp"),
    ("2026-07-14T00:00:00", "2026-07-14T00:00:00Z", False, "invalid_approval_timestamp"),
    ("2026-07-14T00:00:00Z", "2026-07-14T00:00:00Z", False, "approval_expired"),
    ("2026-07-13T23:59:59Z", "2026-07-14T00:00:00Z", False, "approval_expired"),
    ("2026-07-14T00:00:01Z", "2026-07-14T00:00:00Z", True, None),
])
def test_approval_timestamp_validation(expires, now, valid, expected):
    p=plan(); approval=m8r.build_approval_artifact(p, approved_at_utc="2026-07-13T00:00:00Z", expires_at_utc=expires)
    result=m8r.validate_approval_for_plan(approval,p,now_utc=now)
    assert result["valid"] is valid
    if expected:
        assert expected in {i["code"] for i in result["issues"]}


def test_invalid_approved_at_and_now_timestamps_fail_closed():
    p=plan(); approval=m8r.build_approval_artifact(p, approved_at_utc="2026-07-14 00:00:00", expires_at_utc="2026-07-15T00:00:00Z")
    assert "invalid_approval_timestamp" in {i["code"] for i in m8r.validate_approval_for_plan(approval,p,now_utc="2026-07-14T00:00:00Z")["issues"]}
    approval=m8r.build_approval_artifact(p, approved_at_utc="2026-07-14T00:00:00Z", expires_at_utc="2026-07-15T00:00:00Z")
    assert "invalid_approval_timestamp" in {i["code"] for i in m8r.validate_approval_for_plan(approval,p,now_utc="bad-now")["issues"]}

def test_approval_binds_to_exact_plan_and_status():
    p=plan(); approval=m8r.build_approval_artifact(p, approved_at_utc="2026-07-14T00:00:00Z")
    assert m8r.validate_approval_for_plan(approval,p)["valid"]
    for changed in [
        plan(dict(BASE, targets=[{"symbol":"0050","market":"TWSE","instrument_type":"etf"}])),
        plan(dict(BASE, requested_context_types=["liveish_observation"], requested_source_families=["TWSE_MIS"])),
        plan(dict(BASE, requested_context_types=["liveish_observation"])),
        plan(dict(BASE, output_policy={"artifact_root":"research/m8r/planned/other"})),
    ]:
        assert not m8r.validate_approval_for_plan(approval, changed)["valid"]
    for state in ["pending","rejected","expired","consumed"]:
        a=dict(approval, approval_status=state)
        assert not m8r.validate_approval_for_plan(a,p)["valid"]
    expired=dict(approval, expires_at_utc="2026-01-01T00:00:00Z")
    assert not m8r.validate_approval_for_plan(expired,p,now_utc="2026-07-14T00:00:00Z")["valid"]

def test_boundary_no_network_imports_no_adapters_no_terms_no_second_registry():
    src=Path("scripts/m8r_bounded_market_context_request.py").read_text()
    tree=ast.parse(src)
    imports=[]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): imports += [a.name for a in node.names]
        if isinstance(node, ast.ImportFrom) and node.module: imports.append(node.module)
    assert not {"requests","urllib.request","httpx"} & set(imports)
    assert "execute_" not in src and "Session" not in src
    assert "M9" not in m8r.accepted_source_families()
    assert "recommendation" in m8r.NON_GOAL_FLAGS and m8r.NON_GOAL_FLAGS["recommendation"] is False
    assert m8r.SOURCE_REGISTRY_PATH == "docs/data_capabilities/m8_source_capability_registry.json"
