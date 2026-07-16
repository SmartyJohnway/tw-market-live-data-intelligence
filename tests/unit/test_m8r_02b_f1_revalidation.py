from pathlib import Path
import json
import pytest

from scripts.discover_m8r_taifex_option_contracts import SCHEMA_VERSION, discover_openapi, merge_identities
from scripts.m8b_taifex_openapi_client import TaifexOpenApiError
from scripts.m8r_02b_f1_evidence import F1EvidenceConsistencyError, validate_m8r_02b_f1_evidence_consistency


REMOTE_SHA = "08d18d9c6c3cfe0f5307c7dfd19afb8ad0d7af49"

def openapi_row(product="TXO", month="202607", strike="40000", call_put="買權", session="一般"):
    return {"Contract": product, "ContractMonth(Week)": month, "StrikePrice": strike, "CallPut": call_put, "TradingSession": session, "Open": "1", "High": "1", "Low": "1", "Close": "1", "Volume": "1", "OpenInterest": "1"}


def test_openapi_monthly_identity_discovery_returns_exact_identities_no_raw_values():
    result = discover_openapi("TXO", "TX", "202607", "regular", fetcher=lambda endpoint: {"rows": [openapi_row(), openapi_row(strike="41000", call_put="賣權")]})
    assert result["status"] == "succeeded"
    assert result["network_request_count"] == 1
    assert result["contract_count"] == 2
    assert result["row_count_received"] == 2
    assert result["schema_valid_row_count"] == 2
    assert result["matching_product_month_row_count"] == 2
    assert {i["call_put"] for i in result["exact_contract_identities"]} == {"C", "P"}
    serialized = json.dumps(result, ensure_ascii=False).lower()
    for forbidden in ["open_interest", "volume", "bestbid", "bestask", "headers", "cookies", "raw_payload"]:
        assert forbidden not in serialized


def test_openapi_missing_product_month_session_and_zero_rows_fail_closed():
    assert discover_openapi("TXO", "TX", "202607", "regular", fetcher=lambda endpoint: {"rows": [openapi_row(product="ABC")]})["status"] == "no_matching_scope"
    assert discover_openapi("TXO", "TX", "202607", "regular", fetcher=lambda endpoint: {"rows": [openapi_row(month="202608")]})["status"] == "no_matching_scope"
    assert discover_openapi("TXO", "TX", "202607", "regular", fetcher=lambda endpoint: {"rows": [openapi_row(session="盤後")]})["status"] == "no_matching_scope"
    zero = discover_openapi("TXO", "TX", "202607", "regular", fetcher=lambda endpoint: {"rows": []})
    assert zero["status"] == "no_matching_scope"
    assert zero["reason_code"] == "no_matching_contract_identity"


def test_openapi_overall_unavailable_interpreted_correctly():
    def unavailable(endpoint):
        raise TaifexOpenApiError("source_unavailable", {"raw_payload_retained": False})
    result = discover_openapi("TXO", "TX", "202607", "regular", fetcher=unavailable)
    assert result["status"] == "source_unavailable"
    assert result["contract_count"] == 0
    assert result["reason_code"] == "source_unavailable"


def test_bounded_discovery_schema_no_auto_selection_and_cross_source_merge():
    results={
        'TAIFEX_MIS': {'exact_contract_identities':[{'strike':'40000','call_put':'C','product':'TXO','underlying':'TX','expiry':'202607','session':'regular','source_evidence':['TAIFEX_MIS']}]},
        'TAIFEX_OPENAPI': {'exact_contract_identities':[{'strike':'40000','call_put':'C','product':'TXO','underlying':'TX','expiry':'202607','session':'regular','source_evidence':['TAIFEX_OPENAPI']}]} }
    exact=merge_identities(results)
    artifact={'schema_version':SCHEMA_VERSION,'exact_contract_identities':exact,'raw_payload_retained':False,'operator_selection_required':True}
    assert artifact['schema_version']=='m8r_taifex_option_contract_discovery.v1'
    assert artifact['operator_selection_required'] is True
    assert artifact['raw_payload_retained'] is False
    assert exact[0]['source_evidence']==['TAIFEX_MIS','TAIFEX_OPENAPI']
    assert 'selected' not in str(artifact).lower()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def make_case(root: Path, case_id: str, target, returned, result="passed_with_caveats"):
    receipt = root / "cases" / case_id / f"receipt-{case_id}"
    write_json(receipt / "execution_plan.json", {"targets": [target]})
    target_id = f"TAIFEX:option:{target['symbol']}:{target['underlying']}:{target['expiry']}:{target['strike']}:{target['call_put']}:monthly"
    write_json(receipt / "approval_record.json", {"approved_scope": {"target_ids": [target_id]}, "approved_at_utc": "2026-07-15T12:00:02Z"})
    write_json(receipt / "execution_receipt.json", {"execution_started_at_utc": "2026-07-15T12:00:03Z"})
    write_json(receipt / "operation_results.json", [{"returned_identity": returned}])
    write_json(root / "cases" / case_id / "validation_case_result.json", {"case_id": case_id, "result": result, "ai_package_id": "amc-test", "ai_validation": {"valid": True}})


def test_f1_consistency_validation_accepts_finalized_cross_source_evidence(tmp_path):
    root = tmp_path / "run"
    selected = {"product":"TXO","underlying":"TX","expiry":"202607","strike":"40000","call_put":"C","session":"regular"}
    write_json(root / "taifex_option_contract_discovery.json", {"schema_version": SCHEMA_VERSION, "discovery_id":"d1", "completed_at_utc":"2026-07-15T12:00:01Z", "source_results":{"TAIFEX_MIS":{"status":"succeeded"},"TAIFEX_OPENAPI":{"status":"succeeded"}}, "exact_contract_identities":[selected | {"source_evidence":["TAIFEX_MIS","TAIFEX_OPENAPI"]}]})
    write_json(root / "operator_selected_option_contract.json", {"selected_by_operator": True, "authorization_source":"user_instruction", "authorization_recorded_at_utc":"2026-07-15T12:00:02Z", "authorization_reference":"unit_test_authorized_selection", "selected_at_utc":"2026-07-15T12:00:02Z", "selected_contract": selected, "discovery_id":"d1"})
    target = {"symbol":"TXO", "underlying":"TX", "expiry":"202607", "strike":"40000", "call_put":"C", "session":"regular", "derivative_identity": {"underlying":"TX", "expiry":"202607", "strike":"40000", "call_put":"C", "session":"regular"}}
    for cid in ["TAIFEX_MIS_OPTION_EXACT", "TAIFEX_OPENAPI_OPTION_EXACT"]:
        make_case(root, cid, target, selected)
    for cid in ["TPEX_OPENAPI_EOD_6488", "TAIFEX_MIS_FUTURE_EXACT"]:
        write_json(root / "cases" / cid / "validation_case_result.json", {"case_id": cid, "result": "passed_with_caveats", "ai_package_id": "amc-test", "ai_validation": {"valid": True}})
    write_json(root / "f1_revalidation_manifest.json", {"finalized": True, "f1_network_execution_performed": True, "historical_source_execution_artifacts_unchanged": True, "f1_execution_artifacts_new": True, "live_execution_code_base_commit_sha": REMOTE_SHA, "live_execution_patch_commit_sha": REMOTE_SHA})
    write_json(root / "option_live_execution_manifest.json", {"manifest_role":"option_live_execution_run", "finalized": True, "network_execution_performed": True})
    write_json(root / "f1_revalidation_summary.json", {"retention_audit": {"status":"passed"}})
    assert validate_m8r_02b_f1_evidence_consistency(root)["valid"] is True


def test_f1_consistency_validation_rejects_incomplete_source_evidence(tmp_path):
    root = tmp_path / "run"
    selected = {"product":"TXO","underlying":"TX","expiry":"202607","strike":"40000","call_put":"C","session":"regular"}
    write_json(root / "taifex_option_contract_discovery.json", {"schema_version": SCHEMA_VERSION, "discovery_id":"d1", "completed_at_utc":"2026-07-15T12:00:01Z", "source_results":{"TAIFEX_MIS":{"status":"succeeded"},"TAIFEX_OPENAPI":{"status":"succeeded"}}, "exact_contract_identities":[selected | {"source_evidence":["TAIFEX_MIS"]}]})
    write_json(root / "operator_selected_option_contract.json", {"selected_by_operator": True, "authorization_source":"user_instruction", "authorization_recorded_at_utc":"2026-07-15T12:00:02Z", "authorization_reference":"unit_test_authorized_selection", "selected_at_utc":"2026-07-15T12:00:02Z", "selected_contract": selected, "discovery_id":"d1"})
    write_json(root / "f1_revalidation_manifest.json", {"finalized": True, "f1_network_execution_performed": True, "historical_source_execution_artifacts_unchanged": True, "f1_execution_artifacts_new": True, "live_execution_code_base_commit_sha": REMOTE_SHA, "live_execution_patch_commit_sha": REMOTE_SHA})
    write_json(root / "option_live_execution_manifest.json", {"manifest_role":"option_live_execution_run", "finalized": True, "network_execution_performed": True})
    with pytest.raises(F1EvidenceConsistencyError) as exc:
        validate_m8r_02b_f1_evidence_consistency(root)
    assert exc.value.reason_code == "f1_selected_contract_source_evidence_incomplete"


def test_historical_and_new_evidence_separation_contract():
    manifest={'schema_version':'m8r_02b_f1_revalidation_manifest.v1','historical_validation_run_id':'m8r02b-20260715T020000Z','revalidation_run_id':'m8r02b-f1-20260715T120000Z'}
    assert manifest['historical_validation_run_id'] != manifest['revalidation_run_id']


def build_valid_root(tmp_path):
    root = tmp_path / "run_valid"
    selected = {"product":"TXO","underlying":"TX","expiry":"202607","strike":"40000","call_put":"C","session":"regular"}
    write_json(root / "taifex_option_contract_discovery.json", {"schema_version": SCHEMA_VERSION, "discovery_id":"d1", "completed_at_utc":"2026-07-15T12:00:01Z", "source_results":{"TAIFEX_MIS":{"status":"succeeded"},"TAIFEX_OPENAPI":{"status":"succeeded"}}, "exact_contract_identities":[selected | {"source_evidence":["TAIFEX_MIS","TAIFEX_OPENAPI"]}]})
    write_json(root / "operator_selected_option_contract.json", {"selected_by_operator": True, "authorization_source":"user_instruction", "authorization_recorded_at_utc":"2026-07-15T12:00:02Z", "authorization_reference":"unit_test_authorized_selection", "selected_at_utc":"2026-07-15T12:00:02Z", "selected_contract": selected, "discovery_id":"d1"})
    target = {"symbol":"TXO", "underlying":"TX", "expiry":"202607", "strike":"40000", "call_put":"C", "session":"regular", "derivative_identity": {"underlying":"TX", "expiry":"202607", "strike":"40000", "call_put":"C", "session":"regular"}}
    for cid in ["TAIFEX_MIS_OPTION_EXACT", "TAIFEX_OPENAPI_OPTION_EXACT"]:
        make_case(root, cid, target, selected)
    for cid in ["TPEX_OPENAPI_EOD_6488", "TAIFEX_MIS_FUTURE_EXACT"]:
        write_json(root / "cases" / cid / "validation_case_result.json", {"case_id": cid, "result": "passed_with_caveats", "ai_package_id": "amc-test", "ai_validation": {"valid": True}})
    write_json(root / "f1_revalidation_manifest.json", {"finalized": True, "f1_network_execution_performed": True, "historical_source_execution_artifacts_unchanged": True, "f1_execution_artifacts_new": True, "live_execution_code_base_commit_sha": REMOTE_SHA, "live_execution_patch_commit_sha": REMOTE_SHA})
    write_json(root / "option_live_execution_manifest.json", {"manifest_role":"option_live_execution_run", "finalized": True, "network_execution_performed": True})
    write_json(root / "f1_revalidation_summary.json", {"retention_audit": {"status":"passed"}})
    return root


def test_selection_without_operator_authorization_rejected(tmp_path):
    root = build_valid_root(tmp_path)
    selection = json.loads((root / "operator_selected_option_contract.json").read_text())
    selection.pop("authorization_source")
    write_json(root / "operator_selected_option_contract.json", selection)
    with pytest.raises(F1EvidenceConsistencyError) as exc:
        validate_m8r_02b_f1_evidence_consistency(root)
    assert exc.value.reason_code == "f1_operator_selection_not_authorized"



def test_arbitrary_non_empty_authorization_string_rejected(tmp_path):
    root = build_valid_root(tmp_path)
    selection = json.loads((root / "operator_selected_option_contract.json").read_text())
    selection.pop("authorization_source", None)
    selection.pop("authorization_recorded_at_utc", None)
    selection["operator_authorization_reference"] = "non_empty_but_unstructured"
    write_json(root / "operator_selected_option_contract.json", selection)
    with pytest.raises(F1EvidenceConsistencyError) as exc:
        validate_m8r_02b_f1_evidence_consistency(root)
    assert exc.value.reason_code == "f1_operator_selection_not_authorized"

def test_unresolvable_execution_sha_rejected(tmp_path):
    root = build_valid_root(tmp_path)
    manifest = json.loads((root / "f1_revalidation_manifest.json").read_text())
    manifest["live_execution_patch_commit_sha"] = "0" * 40
    write_json(root / "f1_revalidation_manifest.json", manifest)
    with pytest.raises(F1EvidenceConsistencyError) as exc:
        validate_m8r_02b_f1_evidence_consistency(root)
    assert exc.value.reason_code == "f1_execution_commit_not_resolvable"


def test_remote_ancestor_execution_sha_accepted(tmp_path):
    root = build_valid_root(tmp_path)
    assert validate_m8r_02b_f1_evidence_consistency(root)["valid"] is True


def test_option_subrun_finalized_false_rejected(tmp_path):
    root = build_valid_root(tmp_path)
    write_json(root / "option_live_execution_manifest.json", {"manifest_role":"option_live_execution_run", "finalized": False, "network_execution_performed": True})
    with pytest.raises(F1EvidenceConsistencyError) as exc:
        validate_m8r_02b_f1_evidence_consistency(root)
    assert exc.value.reason_code == "f1_option_run_manifest_not_finalized"


def test_option_subrun_network_execution_false_rejected(tmp_path):
    root = build_valid_root(tmp_path)
    write_json(root / "option_live_execution_manifest.json", {"manifest_role":"option_live_execution_run", "finalized": True, "network_execution_performed": False})
    with pytest.raises(F1EvidenceConsistencyError) as exc:
        validate_m8r_02b_f1_evidence_consistency(root)
    assert exc.value.reason_code == "f1_option_run_network_provenance_invalid"
