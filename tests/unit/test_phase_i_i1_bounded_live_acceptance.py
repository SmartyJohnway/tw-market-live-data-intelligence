from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.run_phase_i_i1_bounded_live_acceptance import (
    BoundedTransport,
    OWNER_AUTHORITY_REFERENCE,
    _assert_dormant_authority,
    classify_acceptance,
    run_acceptance,
)
from server.services.phase_i_i1_production_candidate import SOURCE_DESCRIPTORS


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-30T03:00:00Z"


def _json_body(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _fmt(date="1150929"):
    return {"Date": date, "TradeVolume": "1200", "TradeValue": "345600", "Transaction": "42", "TAIEX": "23000.25", "Change": "-12.5"}


def _breadth(date="1150929"):
    return {"出表日期": date, "類型": "股票", "上漲": "4", "漲停": "1", "下跌": "3", "跌停": "0", "持平": "2", "未成交": "1", "無比價": "0"}


def _tpex(date="1150929"):
    return {"Date": date, "DailyTradingValue": "12.5", "DailyTradingVolume": "23.4", "CloseIndex": "200.5", "IndexChange": "-1.25", "PriceRiseCompanyNumbers": "4", "LimitUpCompanyNumbers": "1", "PriceDeclineCompanyNumbers": "3", "LimitDownCompanyNumbers": "0", "PriceFlatCompanyNumbers": "2", "UnmatchedCompanyNumbersSuspensionStocksIncluded": "1"}


def _fixture_identity(monkeypatch):
    snapshot = json.loads((ROOT / "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json").read_text(encoding="utf-8"))
    records = copy.deepcopy(snapshot["records"])
    for record in records:
        classification = record.get("classification") or {}
        identity = record.get("identity") or {}
        if record.get("canonical_target_id") and identity.get("security_code"):
            record["current_listing"] = {"market": classification.get("market"), "security_code": identity["security_code"]}
        if (record.get("classification") or {}).get("instrument_family") == "company_share" and (record.get("classification") or {}).get("instrument_type") == "common_share":
            record.setdefault("execution_eligibility", {})["status"] = "allowed"
            record.setdefault("observation", {})["status"] = "observed_in_latest_verified_snapshot"
    by_canonical = {item["canonical_target_id"]: item for item in records}
    by_code = {}
    by_isin = {}
    by_name = {}
    for record in records:
        ident = record.get("identity") or {}
        market = (record.get("classification") or {}).get("market")
        code = ident.get("security_code")
        if code:
            by_code.setdefault((market, code), []).append(record)
            by_code.setdefault((None, code), []).append(record)
        if ident.get("isin"):
            by_isin.setdefault(ident["isin"].upper(), []).append(record)
    pointer = {
        "schema_version": "taiwan_market_identity_active_pointer.v1",
        "release_id": "fixture-i1-acceptance",
        "release_index_sha256": "a" * 64,
        "release_manifest_sha256": "b" * 64,
    }
    runtime = SimpleNamespace(
        pointer=pointer,
        lookup={"snapshot": {"snapshot_id": pointer["release_id"]}, "by_canonical": by_canonical,
                "by_code": by_code, "by_isin": by_isin, "by_name": by_name},
        validation={"valid": True},
    )
    service = SimpleNamespace(records=records)
    release = {"release_id": pointer["release_id"]}
    manifest = {"release_manifest_sha256": pointer["release_manifest_sha256"]}
    monkeypatch.setattr("scripts.run_phase_i_i1_bounded_live_acceptance.get_production_mode_a_security_master", lambda: runtime)
    monkeypatch.setattr("server.services.unified_mode_a.get_production_mode_a_security_master", lambda *_args, **_kwargs: runtime)
    monkeypatch.setattr("scripts.m8r_08g_security_master_releases.load_active_identity_service", lambda **_kwargs: (service, pointer, release, manifest))
    return runtime


def _fixture_transport(calls):
    payloads = {
        SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]: [_fmt()],
        SOURCE_DESCRIPTORS["I1-TWSE-BREADTH-TWTAZU-OPENAPI"]["url"]: [_breadth()],
        SOURCE_DESCRIPTORS["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["url"]: [_tpex()],
    }

    def transport(url, timeout):
        calls.append((url, timeout))
        return 200, {"Content-Type": "application/json; charset=utf-8"}, _json_body(payloads[url])

    return transport


def test_runner_offline_e2e_uses_candidate_registry_and_shared_market_fetches(tmp_path, monkeypatch):
    _fixture_identity(monkeypatch)
    live_ledger = ROOT / "docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json"
    ledger_before = live_ledger.read_bytes() if live_ledger.exists() else None
    delegated = []
    result = run_acceptance(
        transport=_fixture_transport(delegated),
        security_master_root=tmp_path / "fixture-security-master",
        output_root=tmp_path / "acceptance",
        execution_timestamp=NOW,
        write_governance_ledger=False,
    )

    assert result["status"] == "PASS"
    assert result["owner_authorization_reference"] == OWNER_AUTHORITY_REFERENCE
    assert len(result["security_master"]["selected_targets"]) == 4
    assert len(delegated) == 3
    assert len({url for url, _ in delegated}) == 3
    assert result["network"]["actual_get_count"] == 3
    assert result["market_evidence"]["same_market_reuse"] == {
        "TWSE_targets": 2, "TWSE_source_gets": 2, "TPEX_targets": 2, "TPEX_source_gets": 1,
    }
    assert result["projection"]["result_v3"]["schema_valid"] is True
    assert result["projection"]["audit_v3"]["schema_valid"] is True
    assert result["projection"]["citation_lineage_valid"] is True
    assert result["network"]["raw_payload_persistence"] == "NONE"
    assert result["normal_runtime_dormancy"]["normal_registry_i1_routes"] == 0
    assert _assert_dormant_authority()["active_source_count"] == 0
    assert live_ledger.read_bytes() == ledger_before if ledger_before is not None else not live_ledger.exists()


def test_runner_transport_failure_is_recorded_once_and_stops_without_projection(tmp_path, monkeypatch):
    _fixture_identity(monkeypatch)
    delegated = []

    def failing_transport(url, timeout):
        delegated.append((url, timeout))
        raise OSError("fixture transport unavailable")

    result = run_acceptance(
        transport=failing_transport,
        security_master_root=tmp_path / "fixture-security-master",
        output_root=tmp_path / "acceptance",
        execution_timestamp=NOW,
        write_governance_ledger=False,
    )

    assert result["status"] == "BLOCKED"
    assert result["network_get_count"] == 1
    assert result["retry_count"] == 0
    assert result["claim_state"] == "consumed_failed"
    assert len(delegated) == 1
    assert not list((tmp_path / "acceptance").rglob("*result.v3.json"))


def test_bounded_transport_rejects_repeat_without_second_network_call():
    url = SOURCE_DESCRIPTORS["I1-TWSE-FMTQIK-OPENAPI"]["url"]
    delegated = []
    body = _json_body([_fmt()])
    budget = BoundedTransport(lambda requested, timeout: (delegated.append((requested, timeout)) or (200, {"Content-Type": "application/json"}, body)))
    budget(url, 15)
    with pytest.raises(Exception, match="live_get_budget_exceeded"):
        budget(url, 15)
    assert delegated == [(url, 15)]
    assert len(budget.calls) == 1


def test_bounded_transport_enforces_three_unique_endpoint_maximum():
    urls = [item["url"] for item in SOURCE_DESCRIPTORS.values()]
    delegated = []
    body = _json_body([_fmt()])
    budget = BoundedTransport(lambda url, timeout: (delegated.append((url, timeout)) or (200, {"Content-Type": "application/json"}, body)))
    for url in urls:
        budget(url, 15)
    with pytest.raises(Exception, match="live_get_budget_exceeded"):
        budget(urls[0], 15)
    assert len(delegated) == 3
    assert len(budget.calls) == 3


@pytest.mark.parametrize("kwargs,expected", [
    ({"transport_blocked": False, "network_bounds_proven": True, "twse_status": "partial", "tpex_status": "complete", "result_valid": True, "audit_valid": True, "citation_valid": True, "raw_payload_absent": True, "runtime_dormant": True}, "PASS"),
    ({"transport_blocked": True, "network_bounds_proven": True, "twse_status": "source_failed", "tpex_status": "complete", "result_valid": False, "audit_valid": False, "citation_valid": False, "raw_payload_absent": True, "runtime_dormant": True}, "BLOCKED"),
    ({"transport_blocked": False, "network_bounds_proven": False, "twse_status": "complete", "tpex_status": "complete", "result_valid": True, "audit_valid": True, "citation_valid": True, "raw_payload_absent": True, "runtime_dormant": True}, "FAIL"),
])
def test_acceptance_classification_is_deterministic(kwargs, expected):
    assert classify_acceptance(**kwargs) == expected
