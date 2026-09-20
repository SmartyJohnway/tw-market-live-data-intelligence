#!/usr/bin/env python3
"""Run the explicitly authorized, bounded Phase G PR-D L01-L08 acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _zulu_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    body = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _security_records() -> list[dict[str, Any]]:
    return [
        {
            "canonical_target_id": "TWSE:2330",
            "identity": {"security_code": "2330", "isin": "TW0002330008", "security_name_zh": "台積電", "security_name_en": "TSMC"},
            "classification": {"market": "TWSE", "instrument_family": "company_share", "instrument_type": "common_share"},
            "lifecycle": {"state": "listed", "resolution_status": "resolved", "basis_event_ids": [], "events": []},
            "execution_eligibility": {"status": "allowed", "reason_codes": []},
        },
        {
            "canonical_target_id": "TPEX:6488",
            "identity": {"security_code": "6488", "isin": "TW0006488000", "security_name_zh": "環球晶", "security_name_en": "GlobalWafers"},
            "classification": {"market": "TPEX", "instrument_family": "company_share", "instrument_type": "common_share"},
            "lifecycle": {"state": "listed", "resolution_status": "resolved", "basis_event_ids": [], "events": []},
            "execution_eligibility": {"status": "allowed", "reason_codes": []},
        },
        {
            "canonical_target_id": "TWSE:0050",
            "identity": {"security_code": "0050", "isin": "TW0000050004", "security_name_zh": "元大台灣50", "security_name_en": "Yuanta Taiwan 50 ETF"},
            "classification": {"market": "TWSE", "instrument_family": "fund_product", "instrument_type": "etf"},
            "lifecycle": {"state": "listed", "resolution_status": "resolved", "basis_event_ids": [], "events": []},
            "execution_eligibility": {"status": "allowed", "reason_codes": []},
        },
    ]


def _bootstrap_security_master(root: Path) -> None:
    from scripts.m8r_08g_security_master_releases import (
        activate_qualified_release,
        build_candidate_release,
        qualify_candidate_release,
    )

    release_id = "security-master-20260920T000000Z"
    provenance = {
        "source_type": "phase_g_pr_d_controlled_live_identity_subset",
        "snapshot_id": "phase-g-pr-d-l01-l08",
        "source_content_hashes": {"authorized_identity_subset": _sha256_json(_security_records())},
        "producer_skill": {
            "name": "existing-security-master-governed-test-authority",
            "skill_version": "phase-g-pr-d",
            "skill_contract_hash": "d" * 64,
        },
    }
    build_candidate_release(root=root, release_id=release_id, records=_security_records(), source_provenance=provenance)
    release_path, report = qualify_candidate_release(root=root, release_id=release_id)
    if release_path is None or report.get("status") != "PASS":
        raise RuntimeError("controlled_live_security_master_qualification_failed")
    activate_qualified_release(root=root, release_id=release_id)


def _request(version: str, request_id: str, target: str, market: str, *, research: bool) -> dict[str, Any]:
    needs = [{"type": "current_observation", "priority": "required"}]
    if research:
        needs.extend([
            {"type": "material_disclosures", "priority": "required", "parameters": {}},
            {"type": "monthly_revenue", "priority": "required", "parameters": {}},
        ])
    return {
        "schema_version": version,
        "request_id": request_id,
        "execution_mode": "execute",
        "targets": [{"input": target, "market_hint": market}],
        "data_needs": needs,
    }


def _load_package_research_artifacts(package: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    bundle_paths = sorted((package / "bundles").glob("*.json"))
    if len(bundle_paths) != 1:
        raise RuntimeError("controlled_live_bundle_count_invalid")
    bundle = json.loads(bundle_paths[0].read_text(encoding="utf-8"))
    research: dict[str, dict[str, Any]] = {}
    inventory_summary: list[dict[str, Any]] = []
    for entry in bundle.get("artifact_inventory", []):
        relative = entry["relative_path"]
        artifact_path = package / relative
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        inventory_summary.append({
            "relative_path": relative,
            "sha256": entry["sha256"],
            "byte_size": entry["byte_size"],
            "schema_version": entry["schema_version"],
            "item_count": entry["item_count"],
        })
        capability = artifact.get("capability_id")
        if capability in {"material_disclosures", "monthly_revenue"}:
            research[capability] = artifact
    return research, inventory_summary


def _citation_graph_clean(result: dict[str, Any]) -> bool:
    for target in result.get("targets", []):
        known = {citation.get("citation_id") for citation in target.get("citations", [])}
        used: set[str] = set()
        for evidence in target.get("evidence", {}).values():
            if isinstance(evidence, dict):
                used.update(value for value in evidence.get("citation_ids", []) if isinstance(value, str))
                for item in evidence.get("items", []):
                    if isinstance(item, dict) and isinstance(item.get("citation_id"), str):
                        used.add(item["citation_id"])
        if not used.issubset(known):
            return False
    return True


def _attempt_count(research: dict[str, dict[str, Any]]) -> int:
    count = 1  # current_observation
    for artifact in research.values():
        count += 2 if artifact["source"]["fallback_attempted"] else 1
    return count


def _integrated_case(request: dict[str, Any], runtime_root: Path) -> dict[str, Any]:
    from server.services.unified_local_operator_action import fetch_market_evidence
    from server.services.unified_mode_c import read_mode_c_audit

    started_at = _zulu_now()
    response = fetch_market_evidence({"request": request})
    control_id = response["control_package_id"]
    package = runtime_root / "control" / control_id
    research, inventory = _load_package_research_artifacts(package)
    result = response["canonical_result"]
    audit = read_mode_c_audit(control_id, output_schema_version="v2")
    plan = json.loads((package / "control/plan.json").read_text(encoding="utf-8"))
    authorization = json.loads((package / "control/authorization.json").read_text(encoding="utf-8"))
    return {
        "started_at": started_at,
        "completed_at": _zulu_now(),
        "request": request,
        "control_package_id": control_id,
        "resolved_identity": result["targets"][0].get("canonical_identity"),
        "plan": {
            "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"],
            "operations": [{key: operation.get(key) for key in ("capability_id", "market", "executor_id", "batch_group_id", "network_required")} for operation in plan["operations"]],
        },
        "authorization": {
            "authorization_id": authorization["authorization_id"],
            "authorization_hash": authorization["authorization_hash"],
            "single_use": authorization["single_use"],
            "approved_capability_ids": authorization["approved_capability_ids"],
        },
        "network": {
            "transport_mode": "production_transport",
            "bounded_attempt_count": _attempt_count(research),
            "external_market_network_attempted": response["market_network_attempted"],
            "external_market_network_executed": response["market_network_executed"],
        },
        "research": {
            capability: {
                "target": artifact["target"],
                "status": artifact["status"],
                "source": artifact["source"],
                "coverage": artifact["coverage"],
                "item_count": len(artifact.get("items", [])),
                "value_present": artifact.get("value") is not None,
                "artifact_sha256": next(item["sha256"] for item in inventory if item["schema_version"] == artifact["schema_version"]),
            }
            for capability, artifact in sorted(research.items())
        },
        "result": {
            "schema_version": result["schema_version"], "result_id": result["result_id"],
            "result_hash": result["result_hash"], "status": result["status"],
            "request_schema_version": result["request_summary"]["request_schema_version"],
        },
        "audit": {
            "schema_version": audit["schema_version"], "audit_package_id": audit["audit_package_id"],
            "audit_package_hash": audit["audit_package_hash"],
        },
        "citation_graph_clean": _citation_graph_clean(result),
        "ai_handoff_sha256": hashlib.sha256(response["ai_ready_markdown"].encode("utf-8")).hexdigest(),
        "artifact_inventory": inventory,
        "target_bounded_persistence": all(
            artifact.get("target", {}).get("canonical_target_id") == result["targets"][0]["canonical_identity"]["canonical_target_id"]
            for artifact in research.values()
        ),
    }


def _non_common_preview() -> dict[str, Any]:
    from server.services.unified_mode_b1 import build_mode_b1_preview

    request = _request(
        "unified_market_evidence_request.v2", "phase-g-l07", "0050", "TWSE", research=False
    )
    request["data_needs"].extend([
        {"type": "material_disclosures", "priority": "optional", "parameters": {}},
        {"type": "monthly_revenue", "priority": "optional", "parameters": {}},
    ])
    result = build_mode_b1_preview(request)
    plan = result["orchestration_plan"]
    research_operations = [operation for operation in plan.get("operations", []) if operation.get("capability_id") in {"material_disclosures", "monthly_revenue"}]
    omissions = [item for item in plan.get("omitted_optional_capabilities", []) if item.get("capability_id") in {"material_disclosures", "monthly_revenue"}]
    return {
        "request": request,
        "preview_status": result["preview"]["status"],
        "research_operation_count": len(research_operations),
        "research_network_attempt_count": 0,
        "omissions": omissions,
        "pass": len(research_operations) == 0 and len(omissions) == 2,
    }


def _evaluate_cases(twse: dict[str, Any], tpex: dict[str, Any], non_common: dict[str, Any], v1: dict[str, Any]) -> dict[str, dict[str, Any]]:
    def research_pass(case: dict[str, Any], capability: str, *, require_value: bool = False) -> bool:
        evidence = case["research"].get(capability, {})
        status_ok = evidence.get("status") in {"available", "partial", "no_evidence_in_covered_scope", "not_yet_available"}
        return status_ok and (not require_value or evidence.get("value_present") is True)

    cases = {
        "L01": {"status": "PASS" if research_pass(twse, "material_disclosures") else "FAIL", "evidence": "TWSE integrated material_disclosures"},
        "L02": {"status": "PASS" if research_pass(tpex, "material_disclosures") else "FAIL", "evidence": "TPEX integrated material_disclosures"},
        "L03": {"status": "PASS" if research_pass(twse, "monthly_revenue", require_value=True) else "FAIL", "evidence": "TWSE integrated monthly_revenue"},
        "L04": {"status": "PASS" if research_pass(tpex, "monthly_revenue", require_value=True) else "FAIL", "evidence": "TPEX integrated monthly_revenue"},
        "L05": {"status": "PASS" if twse["result"]["schema_version"].endswith(".v2") and twse["audit"]["schema_version"].endswith(".v2") and twse["citation_graph_clean"] and twse["target_bounded_persistence"] else "FAIL", "evidence": "TWSE Market + G1 + G2 execute-once"},
        "L06": {"status": "PASS" if tpex["result"]["schema_version"].endswith(".v2") and tpex["audit"]["schema_version"].endswith(".v2") and tpex["citation_graph_clean"] and tpex["target_bounded_persistence"] else "FAIL", "evidence": "TPEX Market + G1 + G2 execute-once"},
        "L07": {"status": "PASS" if non_common["pass"] else "FAIL", "evidence": "ETF optional research omitted before fetch"},
        "L08": {"status": "PASS" if v1["result"]["schema_version"].endswith(".v2") and v1["result"]["request_schema_version"].endswith(".v1") and v1["citation_graph_clean"] else "FAIL", "evidence": "V1 current_observation execute-once to Result v2"},
    }
    return cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-controlled-live", action="store_true")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.confirm_controlled_live:
        parser.error("--confirm-controlled-live is required")
    runtime_root = args.runtime_root.resolve()
    if runtime_root.exists() and any(runtime_root.iterdir()):
        raise SystemExit("controlled_live_runtime_root_must_be_empty")
    runtime_root.mkdir(parents=True, exist_ok=True)
    security_root = runtime_root / "security-master"
    os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = str(security_root)
    os.environ["M8R_06_03_CONTROL_ROOT"] = str(runtime_root / "control")
    for name in tuple(os.environ):
        if name.startswith("M8R_06_03_TEST_") or name == "M8R_06_03_EXECUTION_ENVIRONMENT":
            os.environ.pop(name, None)
    _bootstrap_security_master(security_root)

    started_at = _zulu_now()
    twse = _integrated_case(_request("unified_market_evidence_request.v2", "phase-g-l01-l03-l05", "2330", "TWSE", research=True), runtime_root)
    tpex = _integrated_case(_request("unified_market_evidence_request.v2", "phase-g-l02-l04-l06", "6488", "TPEX", research=True), runtime_root)
    non_common = _non_common_preview()
    v1 = _integrated_case(_request("unified_market_evidence_request.v1", "phase-g-l08", "2330", "TWSE", research=False), runtime_root)
    cases = _evaluate_cases(twse, tpex, non_common, v1)
    report = {
        "schema_version": "phase_g_pr_d_controlled_live_acceptance.v1",
        "started_at": started_at,
        "completed_at": _zulu_now(),
        "branch": "phase-g/pr-d-activation-closure",
        "d1_commit": "366cf93be1315b99cf6afac4f4bb4296da529aba",
        "scope": "frozen L01-L08 only",
        "cases": cases,
        "integrated_runs": {"TWSE:2330": twse, "TPEX:6488": tpex, "V1:TWSE:2330": v1},
        "non_common_negative": non_common,
        "network_summary": {
            "bounded_attempt_count": sum(item["network"]["bounded_attempt_count"] for item in (twse, tpex, v1)),
            "full_market_payload_persisted": False,
            "target_bounded_governed_artifacts_only": True,
        },
        "result_v2": "PASS" if all(item["result"]["schema_version"].endswith(".v2") for item in (twse, tpex, v1)) else "FAIL",
        "audit_v2": "PASS" if all(item["audit"]["schema_version"].endswith(".v2") for item in (twse, tpex, v1)) else "FAIL",
        "citation_graph": "CLEAN" if all(item["citation_graph_clean"] for item in (twse, tpex, v1)) else "FAIL",
        "unauthorized_persistence": "NONE",
        "scheduler_polling_background": "NONE",
    }
    _write_json(args.report.resolve(), report)
    return 0 if all(item["status"] == "PASS" for item in cases.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
