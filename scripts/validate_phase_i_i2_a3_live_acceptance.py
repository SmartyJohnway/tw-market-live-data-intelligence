"""Offline integrity/replay verification of the I2 A3 single-GET ledger."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.phase_i_i2_a3_live_support import (
    A1_SHA, GOVERNANCE, LEDGER_PATH, OWNER_AUTHORITY, REVIEWED_HEAD, REVIEWED_TREE,
    ROOT, STARTING_MAIN, SUPERSEDED_AUTHORITY, _digest, _json, dormant_authority,
)


def _contained(reference: str) -> Path:
    path = (ROOT / reference).resolve()
    if not path.is_relative_to((GOVERNANCE / "acceptance_runs").resolve()):
        raise ValueError("acceptance_reference_not_contained")
    return path


def validate() -> dict:
    ledger = _json(LEDGER_PATH)
    if (ledger["schema_version"], ledger["status"], ledger["owner_authorization_reference"],
            ledger["superseded_authority"], ledger["superseded_authority_consumed"],
            ledger["superseded_authority_operational_status"], ledger["reviewed_p0_head"],
            ledger["reviewed_p0_tree"], ledger["starting_main"], ledger["get_authorization_consumed"]) != (
            "phase_i_i2_a3_bounded_live_acceptance_ledger.v1", "PASS", OWNER_AUTHORITY,
            SUPERSEDED_AUTHORITY, False, "superseded_without_use", REVIEWED_HEAD, REVIEWED_TREE, STARTING_MAIN, True):
        raise ValueError("live_ledger_authority_or_gate_invalid")
    if _digest(GOVERNANCE / "PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json") != A1_SHA:
        raise ValueError("frozen_a1_hash_drift")
    runtime = dormant_authority()
    if ledger["normal_runtime_dormancy"] != runtime or ledger["production_activation"] != "NOT_AUTHORIZED" or ledger["merge_authorized"]:
        raise ValueError("live_ledger_runtime_boundary_invalid")
    net = ledger["network"]
    if (net["TAIFEX"], net["TWSE"], net["TPEx"], net["maximum_get_count"], net["retry_count"], net["timeout_seconds"],
            net["redirect_policy"], net["redirect_outcome"], net["maximum_response_bytes"], net["endpoint"]) != (
            1, 0, 0, 1, 0, 30, "reject", "none", 2097152, "https://openapi.taifex.com.tw/v1/DailyMarketReportFut"):
        raise ValueError("live_network_bounds_invalid")
    source = ledger["source_telemetry"]
    if source["http_status"] != 200 or source["content_type"] not in {"application/octet-stream", "application/json"}:
        raise ValueError("live_http_or_media_type_invalid")
    if not 0 < source["response_byte_count"] <= 2097152 or not 0 < source["root_row_count"] <= 5000:
        raise ValueError("live_resource_bounds_invalid")
    if source["json_root_type"] != "array" or source["selection_status"] != "selected" or source["selected_binding_count"] != 1:
        raise ValueError("live_source_selection_invalid")
    if source["selected_maximum_official_date"] != max(source["unique_valid_official_dates"]) or source["selected_contract_period"] != min(source["eligible_tx_regular_monthly_periods"]):
        raise ValueError("live_official_date_or_series_selection_invalid")
    projection = ledger["projection"]
    result_path, audit_path = (_contained(projection[name]["path"]) for name in ("result_v3", "audit_v3"))
    for name, path in (("result_v3", result_path), ("audit_v3", audit_path)):
        if _digest(path) != projection[name]["sha256"] or not projection[name]["schema_valid"]:
            raise ValueError("live_projection_hash_invalid")
    result, audit = _json(result_path), _json(audit_path)
    from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker
    for name, obj in (("unified_market_evidence_result.v3", result), ("unified_market_evidence_audit_package.v3", audit)):
        Draft7Validator(_json(ROOT / "schemas" / (name + ".schema.json")), format_checker=FormatChecker()).validate(obj)
    package_root = next(parent for parent in result_path.parents if (parent / "control/request.json").exists())
    receipt_path = next((package_root / "receipts").glob("*.json"))
    bundle_path = next((package_root / "bundles").glob("*.json"))
    claim_path = next((package_root / "claims").glob("*.json"))
    from scripts.m8r_05c.artifact_loader import load_projection_inputs
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
    from scripts.m8r_05c.result_builder import build_result
    from scripts.m8r_05c.audit_package_builder import build_audit_package
    receipt = _json(receipt_path)
    inputs = load_projection_inputs(request_path=str(package_root / "control/request.json"),
        f3_validation_path=str(package_root / "mode_c/f3_validation.json"), plan_path=str(package_root / "control/plan.json"),
        authorization_path=str(package_root / "control/authorization.json"), consumption_binding_path=str(package_root / "control/consumption_binding.json"),
        claim_path=str(claim_path), receipt_path=str(receipt_path), bundle_path=str(bundle_path), artifact_root=str(package_root),
        calculated_at=receipt["finalized_at"], calculated_at_source="receipt.finalized_at")
    if build_result(inputs, output_schema_version="unified_market_evidence_result.v3") != result:
        raise ValueError("live_result_offline_replay_mismatch")
    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v3")
    if build_audit_package(result, inputs, citations, result_path.relative_to(package_root).as_posix(),
            output_schema_version="unified_market_evidence_audit_package.v3") != audit:
        raise ValueError("live_audit_offline_replay_mismatch")
    execution = ledger["governed_execution"]
    claim = _json(claim_path)
    if (claim["state"], claim["attempt_count"], execution["claim_attempt_count"], execution["operation_statuses"]) != ("consumed_success", 1, 1, ["succeeded", "succeeded"]):
        raise ValueError("live_claim_or_operation_semantics_invalid")
    if inputs.authorization["owner_review_reference"] != OWNER_AUTHORITY:
        raise ValueError("live_authorization_owner_mismatch")
    if execution["artifact_inventory"] != inputs.bundle["artifact_inventory"]:
        raise ValueError("live_artifact_inventory_mismatch")
    evidence_schema = _json(ROOT / "schemas/index_futures_context_evidence.v1.schema.json")
    for target in ("TWSE:1101", "TWSE:1102"):
        binding = lineage.bindings[target]["index_futures_context"]
        if binding.status != "succeeded" or len(binding.evidence_artifacts) != 1:
            raise ValueError("live_target_evidence_binding_invalid")
        artifact = binding.evidence_artifacts[0]
        obj = binding.artifact_objects[artifact["relative_path"]]
        Draft202012Validator(evidence_schema, format_checker=FormatChecker()).validate(obj)
        if obj["status"] not in {"complete", "partial"} or obj["alignment_status"] != "not_comparable":
            raise ValueError("live_evidence_not_accepted")
        if obj["citation_ids"] != [_build_citation_id(binding.operation_id, artifact["relative_path"])]:
            raise ValueError("live_citation_identity_invalid")
        if not set(obj["citation_ids"]).issubset(set(citations.target_need_citations[target + "::index_futures_context"])):
            raise ValueError("live_citation_index_invalid")
        if (obj["trade_date"], obj["contract_period"], obj["retrieved_at"], obj["transport"]["retrieved_at"],
                obj["transport"]["response_sha256"], obj["transport"]["response_byte_count"]) != (
                source["selected_maximum_official_date"], source["selected_contract_period"], ledger["acceptance_execution_timestamp"],
                source["retrieved_at"], source["response_sha256"], source["response_byte_count"]):
            raise ValueError("live_same_source_or_timestamp_mismatch")
    archive_path = _contained(ledger["acceptance_package"]["path"])
    if _digest(archive_path) != ledger["acceptance_package"]["sha256"] or ledger["raw_payload_persistence"] != "NONE":
        raise ValueError("live_package_hash_or_raw_policy_failed")
    run_root = archive_path.parent
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            path = (run_root / name).resolve()
            if not path.is_relative_to(run_root.resolve()) or not path.is_file() or archive.read(name) != path.read_bytes():
                raise ValueError("live_zip_member_integrity_failed")
            try:
                value = json.loads(archive.read(name))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(value, list) and any(isinstance(row, dict) and "ContractMonth(Week)" in row and "TradingSession" in row for row in value):
                raise ValueError("raw_taifex_rows_persisted")
    print("Phase I I2-A3 single-GET live ledger: PASS (offline replay; no source calls)")
    return ledger


if __name__ == "__main__":
    validate()
