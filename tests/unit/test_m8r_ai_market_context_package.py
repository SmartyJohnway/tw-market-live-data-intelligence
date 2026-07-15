from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.m8r_ai_market_context_package import *

NOW = "2026-07-15T01:02:03Z"
ROOT = "research/m8r/test_ai_pkg_artifacts"


def stock_target(symbol="2330", market="TWSE"):
    return {"target_id": f"{market}:equity:{symbol}", "market": market, "symbol": symbol, "instrument_type": "equity", "requested_context_types": ["liveish_observation"], "derivative_identity": {}}


def future_target():
    return {"target_id": "TAIFEX:future:TXF", "market": "TAIFEX", "symbol": "TXF", "instrument_type": "future", "requested_context_types": ["liveish_observation"], "derivative_identity": {"expiry": "202607", "contract_type": "monthly", "session": "regular"}}


def option_target():
    return {"target_id": "TAIFEX:option:TXO", "market": "TAIFEX", "symbol": "TXO", "instrument_type": "option", "requested_context_types": ["liveish_observation"], "derivative_identity": {"underlying": "TXO", "expiry": "202607", "strike": "21000", "call_put": "C", "contract_type": "monthly", "session": "regular"}}


def obs(source="TWSE_MIS", timing="liveish_intraday_snapshot", market="TWSE", symbol="2330", typ="equity", ctx="liveish_observation", cur="fresh_intraday_snapshot", ident=None, caveats=None):
    safe_fields = {"last": "100", "currentness": {"status": cur}}
    if ident:
        safe_fields["contract_identity"] = ident
    return {"source_id": source, "source_family": source, "context_type": ctx, "authority_level": "official_undocumented" if source.endswith("MIS") else "official_documented", "timing_class": timing, "source_timestamp": "2026-07-15T01:00:00Z", "retrieved_at_utc": NOW, "market": market, "symbol": symbol, "instrument_type": typ, "currentness": {"status": cur}, "safe_fields": safe_fields, "caveats": caveats or []}


def op(operation_id="op1", target=None, source="TWSE_MIS", timing="liveish_intraday_snapshot", ctx="liveish_observation", cur="fresh_intraday_snapshot", issues=None, caveats=None, status="succeeded"):
    target = target or stock_target()
    observation = obs(source, timing, target["market"], target["symbol"], target["instrument_type"], ctx, cur, target.get("derivative_identity"), caveats)
    return {"operation_id": operation_id, "target_id": target["target_id"], "context_type": ctx, "source_family": source, "operation_class": "planned_network_fetch", "status": status, "network_attempted": True, "source_observation": observation if status == "succeeded" else {}, "currentness": {"status": cur}, "issues": issues or []}


def local_op(kind="health", target=None):
    target = target or stock_target()
    if kind == "health":
        return {"operation_id": "lh", "target_id": target["target_id"], "context_type": "source_health", "source_family": None, "operation_class": "local_source_health_read", "status": "succeeded", "network_attempted": False, "source_observation": {"source_id": "LOCAL_SOURCE_HEALTH", "source_family": "LOCAL_CONTEXT", "context_type": "source_health", "retrieved_at_utc": NOW, "safe_fields": {"referenced_source_family": "TWSE_MIS", "artifact_availability": "unknown", "staleness_caveat": "not live"}}}
    return {"operation_id": "mc", "target_id": target["target_id"], "context_type": "market_session_state", "source_family": None, "operation_class": "local_market_clock_evaluation", "status": "succeeded", "network_attempted": False, "source_observation": {"source_id": "LOCAL_MARKET_CLOCK", "source_family": "LOCAL_CONTEXT", "context_type": "market_session_state", "retrieved_at_utc": NOW, "safe_fields": {"target_market": target["market"], "market_session_state": "unresolved", "calendar_caveat": "unresolved"}}}


def missing(target=None, ctx="official_eod_reference", source="TWSE_OPENAPI", reason="source_execution_failed"):
    target = target or stock_target()
    return {"target_id": target["target_id"], "context_type": ctx, "planned_source_family": source, "reason_code": reason, "operation_status": "failed"}


def result(status="ready_with_caveats", receipt_id="r1", plan_hash="h1", missing_context=None, operations=None, targets=None, retention=True, core_status="built", include_targets=True):
    targets = targets or [stock_target()]
    operations = operations if operations is not None else [op(target=targets[0])]
    missing_context = missing_context or []
    return {"schema_version": "m8r_market_context_orchestration_result.v1", "execution_status": status, "approved_targets": deepcopy(targets) if include_targets else None, "execution_receipt": {"schema_version": "m8r_market_context_execution_receipt.v1", "receipt_id": receipt_id, "plan_id": "p1", "plan_hash": plan_hash, "approval_id": "a1", "approved_output_scope": {"artifact_root": ROOT}, "execution_started_at_utc": NOW, "execution_finished_at_utc": NOW, "approval_consumed": True, "bounded_retention": retention, "raw_payload_retained": False if retention else True, "full_market_retained_output": False, "approved_target_count": len(targets), "approved_operation_count": len(operations), "successful_context_count": sum(1 for o in operations if o.get("status") == "succeeded" and o.get("operation_class") == "planned_network_fetch"), "missing_context_count": len(missing_context), "network_operations_attempted": sum(1 for o in operations if o.get("network_attempted")), "local_operations_attempted": sum(1 for o in operations if str(o.get("operation_class", "")).startswith("local_")), "package_status": status}, "operation_results": operations, "missing_context": missing_context, "m8_context_core_status": {"status": core_status}, "approval_state": {"approval_id": "a1", "approval_status": "consumed"}}


def build(r, t=NOW):
    return build_ai_market_context_package(r, generated_at_utc=t)


def rehash(pkg):
    pkg["integrity"]["package_hash"] = compute_ai_market_context_hash(build_ai_market_context_hash_scope(pkg))
    pkg["package_id"] = "amc-" + pkg["integrity"]["package_hash"][:16]
    return pkg


def test_identity_determinism_and_hash_boundaries():
    p1 = build(result(), "2026-07-15T01:02:03Z")
    p2 = build(result(), "2026-07-15T02:02:03Z")
    assert p1["package_id"] == p2["package_id"]
    assert build(result(plan_hash="h2"))["package_id"] != p1["package_id"]
    assert build(result(receipt_id="r2"))["package_id"] != p1["package_id"]
    assert build(result(operations=list(reversed(result()["operation_results"]))))["package_id"] == p1["package_id"]


@pytest.mark.parametrize("mutator", [
    lambda p: p["conversation_views"]["compact"].__setitem__("package_status", "ready"),
    lambda p: p["conversation_views"]["compact"]["latest_usable_observations"][0].__setitem__("source_family", "BAD"),
    lambda p: p["conversation_views"]["standard"]["forbidden_interpretations"].remove("not_prediction"),
    lambda p: p["conversation_views"]["standard"].__setitem__("advice", "this is a buying opportunity"),
    lambda p: p["conversation_views"]["diagnostic"]["provenance"].__setitem__("plan_hash", "tampered"),
])
def test_conversation_view_integrity_tampering_fails(mutator):
    pkg = build(result())
    mutator(pkg)
    with pytest.raises(AIMarketContextPackageError, match="conversation_view_mismatch"):
        validate_ai_market_context_package(pkg)
    assert validate_ai_market_context_package(build(result())) == {"status": "valid"}
    assert all(v["package_id"] == build(result())["package_id"] for v in build(result())["conversation_views"].values())


def test_status_input_validation_and_unsafe_retention():
    miss = [missing()]
    assert build(result(status="partial", missing_context=miss, operations=[op(), op(operation_id="op2", status="failed")]))["package_status"] == "partial"
    assert build(result(status="blocked", operations=[], missing_context=miss, targets=[stock_target()]))["package_status"] == "blocked"
    unsafe = build(result(retention=False))
    assert unsafe["package_status"] == "blocked"
    assert any(c["code"] == "unsafe_upstream_retention_contract" for c in unsafe["caveats"])
    for bad in [
        {**result(), "schema_version": "bad"},
        {**result(), "execution_receipt": {**result()["execution_receipt"], "schema_version": "bad"}},
        {**result(), "execution_receipt": {**result()["execution_receipt"], "plan_id": None}},
        {**result(), "execution_receipt": {**result()["execution_receipt"], "approved_operation_count": 99}},
        {**result(), "execution_receipt": {**result()["execution_receipt"], "missing_context_count": 99}},
    ]:
        with pytest.raises(AIMarketContextPackageError):
            build(bad)


def test_source_semantics_structured_caveats_and_currentness():
    ft = future_target()
    ops = [
        op("op0", stock_target(), "TWSE_MIS", "liveish_intraday_snapshot", cur="fresh_intraday_snapshot", caveats=["string_warning"], issues=[{"code": "source_warning", "message": "ok", "error": "secret-token"}]),
        op("op1", stock_target(), "TWSE_OPENAPI", "official_eod", "official_eod_reference", "official_eod_reference"),
        op("op2", stock_target("6488", "TPEX"), "TPEX_OPENAPI", "official_eod", "official_eod_reference", "official_eod_reference"),
        op("op3", ft, "TAIFEX_MIS", "liveish_intraday_snapshot", cur="source_specific_currentness_unresolved"),
        op("op4", ft, "TAIFEX_OPENAPI", "official_statistics_eod", "official_statistical_reference", "stale_official_statistics_eod"),
    ]
    pkg = build(result(operations=ops, targets=[stock_target(), stock_target("6488", "TPEX"), ft]))
    timing = {c["source_family"]: c["timing_class"] for c in pkg["source_contexts"]}
    assert timing == {"TWSE_MIS": "liveish_intraday_snapshot", "TWSE_OPENAPI": "official_eod", "TPEX_OPENAPI": "official_eod", "TAIFEX_MIS": "liveish_intraday_snapshot", "TAIFEX_OPENAPI": "official_statistics_eod"}
    twse = next(c for c in pkg["source_contexts"] if c["source_family"] == "TWSE_MIS")
    assert {c["code"] for c in twse["caveats"]} == {"source_warning", "string_warning"}
    assert "secret-token" not in json.dumps(twse)
    assert pkg["currentness_summary"]["overall_status"] == "mixed"
    assert normalize_currentness_status({"status": "not_current"}) != "current"
    assert normalize_currentness_status({"status": "unknown vocabulary"}) == "unknown"


def test_caveat_determinism_dedup_and_hash_ordering():
    issues1 = [{"code": "warn", "message": "same"}, {"code": "warn", "message": "same"}]
    issues2 = list(reversed(issues1))
    p1 = build(result(operations=[op(issues=issues1, caveats=["a", "b"])]))
    p2 = build(result(operations=[op(issues=issues2, caveats=["b", "a"])]))
    assert p1["package_id"] == p2["package_id"]
    ctx = p1["source_contexts"][0]
    assert len([c for c in ctx["caveats"] if c["code"] == "warn"]) == 1


def test_taifex_identity_future_option_and_missing_only_preserved():
    ft, ot = future_target(), option_target()
    pkg = build(result(operations=[op(target=ft, source="TAIFEX_MIS")], targets=[ft]))
    assert pkg["targets"][0]["derivative_identity"]["expiry"] == "202607"
    pkg2 = build(result(operations=[op(target=ot, source="TAIFEX_MIS")], targets=[ot]))
    assert pkg2["targets"][0]["derivative_identity"]["strike"] == "21000"
    miss_only = build(result(status="blocked", operations=[], targets=[ot], missing_context=[missing(ot, source="TAIFEX_MIS")]))
    assert miss_only["targets"][0]["derivative_identity"]["call_put"] == "C"
    bad = rehash(deepcopy(pkg)); bad["targets"][0]["derivative_identity"].pop("expiry"); rehash(bad); bad["conversation_views"] = build_conversation_views({**bad, "_operation_outcomes": bad["conversation_views"]["diagnostic"]["operation_outcomes"]})
    with pytest.raises(AIMarketContextPackageError):
        validate_ai_market_context_package(bad)


def test_degraded_target_inference_is_partial_and_caveated():
    pkg = build(result(include_targets=False))
    assert pkg["provenance"]["target_identity_provenance"] == "inferred_from_operation_result"
    assert pkg["package_status"] == "partial"
    assert any(c["code"] == "approved_target_scope_not_fully_available" for c in pkg["caveats"])
    bad = result(include_targets=False, operations=[])
    bad["execution_receipt"]["approved_target_count"] = 1
    with pytest.raises(AIMarketContextPackageError):
        build(bad)


def test_local_forbidden_and_views():
    operations = [local_op("health"), local_op("clock")]
    pkg = build(result(status="ready_with_caveats", operations=operations, targets=[stock_target()]))
    assert pkg["source_health_context"] and pkg["market_session_context"]
    assert "local_health_not_live_probe" in pkg["forbidden_interpretations"]
    assert "unresolved_session_not_open_or_closed" in pkg["forbidden_interpretations"]
    assert {"compact", "standard", "diagnostic"} == set(pkg["conversation_views"])


def test_raw_data_safety():
    r = result()
    r["operation_results"][0]["source_observation"]["safe_fields"]["note"] = "raw word in value is ok"
    assert build(r)
    for key in ["raw_payload", "authorization", "cookie"]:
        rr = result()
        rr["operation_results"][0]["source_observation"][key] = "x"
        with pytest.raises(AIMarketContextPackageError):
            build(rr)


def test_extended_validation_cannot_be_bypassed_by_rehashing():
    pkg = build(result())
    cases = []
    bad = deepcopy(pkg); bad["conversation_views"]["compact"]["package_status"] = "ready"; cases.append(bad)
    bad = deepcopy(pkg); bad["targets"][0]["source_context_refs"] = ["missing"]; rehash(bad); cases.append(bad)
    bad = deepcopy(pkg); bad["scope"]["successful_context_count"] = 99; rehash(bad); cases.append(bad)
    bad = deepcopy(pkg); bad["source_contexts"][0]["source_family"] = "UNSAFE"; rehash(bad); cases.append(bad)
    bad = deepcopy(pkg); bad["forbidden_interpretations"].remove("not_prediction"); rehash(bad); cases.append(bad)
    bad = deepcopy(pkg); bad["production_readiness"]["production_live_execution_ready"] = True; rehash(bad); cases.append(bad)
    bad = deepcopy(pkg); bad["package_status"] = "ready"; rehash(bad); cases.append(bad)
    for item in cases:
        with pytest.raises(AIMarketContextPackageError):
            validate_ai_market_context_package(item)


def test_artifacts_bind_approved_root_and_receipt(tmp_path):
    shutil.rmtree(ROOT, ignore_errors=True)
    pkg = build(result(receipt_id="rid-art"))
    files = write_ai_market_context_artifacts(pkg)
    assert all(Path(f).parent.as_posix() == f"{ROOT}/rid-art" for f in files)
    assert {Path(f).name for f in files} == {"ai_market_context_v1.json", "ai_market_context_compact.json", "ai_market_context_standard.json", "ai_market_context_diagnostic.json"}
    with pytest.raises(FileExistsError):
        write_ai_market_context_artifacts(pkg)
    with pytest.raises(OSError, match="approved_output_scope_mismatch"):
        write_ai_market_context_artifacts(pkg, artifact_root="research/m8r/other_safe")
    with pytest.raises(OSError, match="receipt_identity_mismatch"):
        write_ai_market_context_artifacts(pkg, receipt_id="other")
    for root in ["/tmp/x", "research/m8r/../x", "frontend/public/x", "research/generated/x"]:
        p = build(result())
        p["provenance"]["approved_output_scope"]["artifact_root"] = root
        rehash(p); p["conversation_views"] = build_conversation_views({**p, "_operation_outcomes": p["conversation_views"]["diagnostic"]["operation_outcomes"]})
        with pytest.raises(OSError):
            write_ai_market_context_artifacts(p)
    shutil.rmtree(ROOT, ignore_errors=True)


def test_fixture_files_are_small_and_present():
    fixture_dir = Path("tests/fixtures/m8r_ai_market_context")
    names = {p.name for p in fixture_dir.glob("*.json")}
    assert {"complete_twse.json", "blocked_with_target.json", "structured_warning_issue.json", "mixed_currentness.json", "taifex_future.json", "taifex_option.json", "missing_only.json", "unsafe_retention.json"} <= names
    assert all(p.stat().st_size < 12000 for p in fixture_dir.glob("*.json"))


def test_boundary_no_network_or_product_surface_imports():
    text = Path("scripts/m8r_ai_market_context_package.py").read_text()
    banned_imports = ["import requests", "import urllib", "import httpx", "FastAPI", "@app.", "sqlite3"]
    assert not any(item in text for item in banned_imports)
    assert PROD["production_executor_adapters_ready"] is False and PROD["production_live_execution_ready"] is False
