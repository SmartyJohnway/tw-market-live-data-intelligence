"""Offline production-planner proof for the Owner-accepted H3 TWSE route."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
from server.services.unified_contract_versions import (
    PREFERRED_REQUEST_SCHEMA_VERSION,
    REQUEST_CAPABILITY_CATALOG_PATHS,
    REQUEST_SCHEMA_PATHS,
)


ROOT = Path(__file__).resolve().parents[2]
FIXED_TIME = "2026-09-28T00:00:00Z"


class OfflineSecurityMaster:
    """Minimal deterministic identity input; all planning authorities stay real."""

    def __init__(self, market: str, code: str):
        canonical = f"{market}:{code}"
        self.pointer = {
            "schema_version": "taiwan_market_identity_active_pointer.v1",
            "release_id": "offline-preview-fixture",
            "release_index_sha256": "a" * 64,
            "release_manifest_sha256": "b" * 64,
        }
        record = {
            "canonical_target_id": canonical,
            "identity": {
                "security_code": code,
                "isin": "TW0001423007" if code == "1423" else "TW0006488000",
                "security_name_zh": "offline identity fixture",
                "security_name_en": "offline identity fixture",
            },
            "classification": {
                "market": market,
                "instrument_family": "company_share",
                "instrument_type": "common_share",
                "classification_status": "confirmed",
            },
            "execution_eligibility": {"status": "allowed", "reason_codes": []},
            "observation": {"status": "official_snapshot"},
        }
        self.lookup = {
            "snapshot": {"snapshot_id": "offline-preview-fixture", "records": [record]},
            "by_canonical": {canonical: record},
            "by_isin": {record["identity"]["isin"]: [record]},
            "by_code": {(market, code): [record], (None, code): [record]},
            "by_name": {},
        }


def _request(market: str, code: str) -> dict:
    return {
        "schema_version": PREFERRED_REQUEST_SCHEMA_VERSION,
        "request_id": f"h3-candidate-preview-{market.lower()}-{code}",
        "execution_mode": "preview",
        "targets": [{"input": f"{market}:{code}", "market_hint": market}],
        "data_needs": [
            {
                "type": "recent_performance",
                "priority": "required",
                "parameters": {"lookback_trading_days": 20},
            }
        ],
    }


def _production_preview(request: dict, market: str, code: str) -> dict:
    version = request["schema_version"]
    catalog = json.loads(REQUEST_CAPABILITY_CATALOG_PATHS[version].read_text(encoding="utf-8"))
    schema = json.loads(REQUEST_SCHEMA_PATHS[version].read_text(encoding="utf-8"))
    security_master = OfflineSecurityMaster(market, code)
    validation = validate_unified_market_evidence_request(
        request,
        security_master=security_master,
        capability_catalog=catalog,
        request_schema=schema,
        allow_fixture_snapshot=False,
    )
    package = build_mode_b1_preview_package(
        request,
        validation,
        security_master,
        planning_timestamp=FIXED_TIME,
    )
    assert package["network_executed"] is False
    assert package["authorization_created"] is False
    assert package["authorization_consumed"] is False
    assert package["execution_performed"] is False
    return package


def test_production_preview_selects_exact_h3_twse_route_without_authorization_or_network():
    package = _production_preview(_request("TWSE", "1423"), "TWSE", "1423")

    assert package["validation"]["validation_status"] == "valid"
    assert package["validation"]["capability_results"][0]["status"] == "runtime_executable"
    assert package["preview"]["status"] == "ready_for_confirmation"
    assert package["preview"]["bounds"]["operation_count"] == 1
    assert package["preview"]["bounds"]["estimated_network_calls"] == 1
    operations = package["orchestration_plan"]["operations"]
    assert len(operations) == 1
    operation = operations[0]
    assert operation["operation_status"] == "executable_pending_approval"
    assert operation["canonical_target_ids"] == ["TWSE:1423"]
    assert operation["market"] == "TWSE"
    assert operation["executor_id"] == "phase_h_h3_twse_recent_performance_executor"
    assert operation["network_required"] is True
    assert operation["parameters"] == {"lookback_trading_days": 20}


def test_production_preview_keeps_tpex_h3_non_executable_with_zero_network_estimate():
    package = _production_preview(_request("TPEX", "6488"), "TPEX", "6488")

    assert package["validation"]["validation_status"] == "valid"
    assert package["preview"]["status"] != "ready_for_confirmation"
    assert package["preview"]["bounds"]["estimated_network_calls"] == 0
    assert package["orchestration_plan"]["operations"] == []
    blocked = package["orchestration_plan"]["blocked_operations"]
    assert len(blocked) == 1
    assert blocked[0]["capability_id"] == "recent_performance"
    assert blocked[0]["executor_id"] is None
    assert blocked[0]["executor_invocation_eligible"] is False
    assert "unsupported_market" in blocked[0]["blocking_reason_codes"]
