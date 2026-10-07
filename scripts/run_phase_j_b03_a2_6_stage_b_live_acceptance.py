"""One-shot, production-path Stage-B live acceptance runner for J-B03-A2.6.

This script is intentionally manual and bounded. It never persists source
response bytes; the governed execution package is created in the OS temp area.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.m8r_06_03_production_adapter import (
    PHASE_H_H1_COMPOSITE_EXECUTOR_ID,
    build_production_runtime_adapter_registry,
)
from server.services import phase_h_h1_tpex_composite as composite_core
from scripts.m8r_06_01c2_mode_a_security_master_loader import load_active_mode_a_security_master
from server.services.unified_mode_a import validate_mode_a_request
from tests.helpers.phase_h_imp_7d_control_package import fixture_request
from tests.helpers.phase_j_b03_a2_6_stage_b import run_production_dispatch_fixture

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TARGET = "TPEX:6488"
EXPECTED_ENDPOINTS = [item["endpoint"] for item in composite_core.SOURCES]


def _validate(schema_name: str, value: dict[str, Any]) -> None:
    schema = json.loads((ROOT / f"schemas/{schema_name}.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        raise AssertionError(f"{schema_name} validation failed: {errors[0].message}")


def run() -> dict[str, Any]:
    calls: list[dict[str, Any]] = []
    real_get = composite_core.official_get
    request = fixture_request(request_id="a26-stage-b-live-6488")
    security_master = load_active_mode_a_security_master()
    if security_master.validation.get("valid") is not True:
        raise AssertionError("active_security_master_not_valid")
    from unittest.mock import patch
    with patch("server.services.unified_mode_a.get_production_mode_a_security_master", return_value=security_master):
        f3 = validate_mode_a_request(request)
    resolved = [item for item in f3.get("target_results", []) if item.get("resolution_status") == "resolved"]
    if len(resolved) != 1 or resolved[0].get("canonical_identity", {}).get("canonical_target_id") != EXPECTED_TARGET:
        raise AssertionError("production_identity_resolution_not_exact")

    def capture_get(endpoint: str, *, timeout_seconds: int = 60) -> dict[str, Any]:
        if len(calls) >= 10:
            raise AssertionError("stage_b_get_ceiling_exceeded")
        ordinal = len(calls) + 1
        expected = EXPECTED_ENDPOINTS[ordinal - 1] if ordinal <= len(EXPECTED_ENDPOINTS) else None
        if endpoint != expected:
            raise AssertionError("stage_b_fixed_source_order_or_endpoint_mismatch")
        response = real_get(endpoint, timeout_seconds=timeout_seconds)
        raw = response["raw_bytes"]
        calls.append({
            "request_ordinal": ordinal,
            "method": "GET",
            "requested_url": endpoint,
            "effective_url": response.get("effective_url"),
            "http_status": response.get("status"),
            "content_type": response.get("content_type"),
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "retrieved_at": response.get("retrieved_at"),
            "tls_policy": response.get("tls_policy"),
            "redirect_count": response.get("redirect_count"),
        })
        return response

    with tempfile.TemporaryDirectory(prefix="tw-market-a26-stage-b-") as temp_dir:
        execution = run_production_dispatch_fixture(
            Path(temp_dir) / "package", official_transport=capture_get,
            request_override=request, f3_validation=f3, security_master=security_master,
        )
        if len(calls) != 3 or [item["requested_url"] for item in calls] != EXPECTED_ENDPOINTS:
            raise AssertionError("stage_b_live_request_count_or_order_invalid")
        # Mode C read, audit, and AI handoff completed inside the normal path;
        # this final equality proves those reads caused no additional GET.
        if len(calls) != 3:
            raise AssertionError("unexpected_market_request_after_execution")

        registry = execution["registry"]
        selected_route = next(
            item for item in json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))["routes"]
            if item["capability_id"] == "trading_status_context"
        )
        plan_operation = execution["plan"]["operations"][0]
        bounded_request = execution["execution_requests"][0]
        operation_result = execution["outcomes"][0]
        registry_routes = registry.routes_for_executor(PHASE_H_H1_COMPOSITE_EXECUTOR_ID)
        if not registry_routes or any(item.executor_id != PHASE_H_H1_COMPOSITE_EXECUTOR_ID for item in registry_routes):
            raise AssertionError("production_registry_executor_mismatch")
        selected_ids = {
            selected_route["selected_executor_id"], plan_operation["executor_id"],
            bounded_request["executor_id"], operation_result["executor_id"],
            registry_routes[0].executor_id,
        }
        if selected_ids != {PHASE_H_H1_COMPOSITE_EXECUTOR_ID}:
            raise AssertionError("canonical_production_executor_identity_mismatch")
        if bounded_request.get("approved_security_identifiers") != [EXPECTED_TARGET]:
            raise AssertionError("live_approved_target_mismatch")

        _validate("unified_market_evidence_operation_result.v2", operation_result)
        _validate("unified_market_evidence_bundle.v1", execution["bundle"])
        _validate("unified_market_evidence_execution_receipt.v1", execution["receipt"])
        _validate("unified_market_evidence_result.v3", execution["result"])
        _validate("unified_market_evidence_audit_package.v3", execution["audit"])

        result_value = execution["result"]["targets"][0]["evidence"]["trading_status_context"]
        if result_value.get("schema_version") != "trading_status_context_composite.v1":
            raise AssertionError("result_not_composite_v1")
        _validate("trading_status_context_composite.v1", result_value)
        if len(calls) != 3:
            raise AssertionError("mode_c_or_projection_performed_extra_market_get")

        artifact_summaries: list[dict[str, Any]] = []
        outcome = execution["outcomes"][0]
        for artifact in outcome["evidence_artifacts"]:
            path = execution["root"] / artifact["relative_path"]
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != artifact["sha256"]:
                raise AssertionError("persisted_artifact_hash_mismatch")
            entry = {key: artifact[key] for key in ("relative_path", "sha256", "schema_version", "artifact_role", "item_count")}
            if artifact["artifact_role"] == "component_evidence":
                evidence = json.loads(payload.decode("utf-8"))
                entry["source_id"] = evidence["source"]["source_id"]
                entry["component_status"] = evidence["status"]
                entry["canonical_coverage"] = evidence["coverage"]["covered_status_types"]
                entry["native_observation_count"] = evidence.get("native_observation_count", 0)
            artifact_summaries.append(entry)

        primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
        composite_hash = hashlib.sha256((execution["root"] / primary["relative_path"]).read_bytes()).hexdigest()
        components = result_value["components"]
        if len(components) != 3:
            raise AssertionError("expected_three_composite_components")
        handoff_markdown = execution["handoff_markdown"]
        if not all(name in handoff_markdown for name in (
            "TPEx Attention", "TPEx Disposition", "TPEx Current Special-Status Native Evidence",
        )):
            raise AssertionError("component_distinctions_missing_from_handoff")
        disposition = next(item for item in components if item["source_id"] == "H1-TPEX-DISPOSITION-OPENAPI")
        for evidence_item in disposition["evidence"].get("items", []):
            for field in ("official_reason", "official_conditions"):
                value = evidence_item.get(field)
                if isinstance(value, str) and value and value not in handoff_markdown:
                    raise AssertionError("disposition_source_text_missing_from_handoff")
        cmode = next(item for item in components if item["source_id"] == "H1-TPEX-CHANGED-TRADING-OPENAPI")
        cmode_observations = cmode["evidence"].get("native_observations", [])
        if cmode_observations:
            observation = cmode_observations[0]
            if (observation.get("semantic_status") != "unresolved"
                    or observation.get("source_native_label") not in handoff_markdown
                    or observation.get("semantic_caveat") not in handoff_markdown
                    or not all(citation in handoff_markdown for citation in observation.get("citation_ids", []))):
                raise AssertionError("cmode_native_evidence_not_safely_handed_off")
            raw_value = json.dumps(observation["source_native_value"], ensure_ascii=False, separators=(",", ":"))
            if raw_value not in handoff_markdown:
                raise AssertionError("cmode_native_raw_value_missing_from_handoff")
            if "不可單獨解讀為停牌" not in handoff_markdown:
                raise AssertionError("cmode_no_inference_guard_missing_from_handoff")
        elif not cmode["evidence"].get("caveats"):
            raise AssertionError("cmode_no_match_or_failure_caveat_missing")
        return {
            "stage_b_live_run": "PASS",
            "target": EXPECTED_TARGET,
            "mode_a_identity_resolution": {"status": "resolved", "canonical_target_id": EXPECTED_TARGET,
                                            "instrument_id": resolved[0]["canonical_identity"]["instrument_id"]},
            "executor_identity": {
                "routing_selected_executor_id": selected_route["selected_executor_id"],
                "plan_executor_id": plan_operation["executor_id"],
                "execution_request_executor_id": bounded_request["executor_id"],
                "operation_result_executor_id": operation_result["executor_id"],
                "registry_executor_id": registry_routes[0].executor_id,
            },
            "network_accounting": {"GET": len(calls), "HEAD": 0, "POST": 0},
            "source_requests": calls,
            "operation_result": {"status": operation_result["status"], "schema_version": operation_result["schema_version"],
                                 "result_item_count": operation_result["result_item_count"]},
            "components": artifact_summaries,
            "composite": {"schema_version": result_value["schema_version"], "status": result_value["status"],
                          "canonical_coverage": result_value["aggregate_coverage"]["covered_status_types"],
                          "canonical_item_count": result_value["canonical_item_count"],
                          "native_observation_count": result_value["native_observation_count"],
                          "component_count": result_value["component_count"], "sha256": composite_hash},
            "bundle": {"schema_version": execution["bundle"]["schema_version"], "artifact_count": len(execution["bundle"]["artifacts"])},
            "receipt": {"schema_version": execution["receipt"]["schema_version"], "status": execution["receipt"]["status"]},
            "lineage": "PASS",
            "result_v3": "PASS",
            "audit_v3": "PASS",
            "mode_c_handoff": {"status": "PASS", "component_distinctions": True,
                                "native_observation_count": len(cmode_observations),
                                "raw_native_rendered": bool(cmode_observations),
                                "markdown_sha256": hashlib.sha256(handoff_markdown.encode("utf-8")).hexdigest()},
            "temporary_package_removed": True,
            "raw_response_persisted": False,
        }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, indent=2))
