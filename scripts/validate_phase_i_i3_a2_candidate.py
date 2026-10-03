"""Offline technical and governance validator for the dormant I3-A2 candidate."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_phase_i_i3_a1 as a1
from scripts.run_phase_i_i3_a0_preflight import PROTECTED

BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
START = "f773b7b28f2e17d1f038084dc864dd15fbeda1bd"
START_TREE = "f4ce0391bc450d7c6857203b10973f6b540c079a"
OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A2_DORMANT_OFFLINE_IMPLEMENTATION_AUTHORIZATION"
RECORD = "docs/governance/phase_i/PHASE_I_I3_A2_DORMANT_OFFLINE_IMPLEMENTATION_CANDIDATE_2026-10-03.json"
SCHEMA = "schemas/cash_institutional_flow_context_evidence.v1.schema.json"
MODULES = (
    "server/services/phase_i_i3_cash_institutional_flow_adapters.py",
    "server/services/phase_i_i3_cash_institutional_flow_offline_candidate.py",
)
FORBIDDEN_MODULES = {"socket", "urllib.request", "requests", "httpx", "aiohttp", "subprocess"}
FORBIDDEN_PARAMETERS = {"url", "endpoint", "reader", "opener", "client", "session", "transport", "transport_callback"}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_networkless_source(source: str) -> None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                require(not any(name.name == bad or name.name.startswith(bad + ".") for bad in FORBIDDEN_MODULES), "candidate_network_import_forbidden")
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            require(not any(module == bad or module.startswith(bad + ".") for bad in FORBIDDEN_MODULES), "candidate_network_import_forbidden")
            require(not module.startswith("scripts.run_phase_i_i3_a0"), "historical_research_runner_import_forbidden")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = {arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
            require(not params.intersection(FORBIDDEN_PARAMETERS), "candidate_transport_parameter_forbidden")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            require(node.func.attr not in {"now", "utcnow", "time", "urlopen", "create_connection"},
                    "candidate_clock_or_network_call_forbidden")
    require("run_phase_i_i3_a0_preflight" not in source and "run_phase_i_i3_a0_attempt" not in source,
            "historical_research_runner_dependency_forbidden")


def validate(*, require_record: bool = True) -> dict | None:
    def deny(*args, **kwargs):
        raise AssertionError("a2_external_network_forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        a1.validate()
        schema = json.loads((ROOT / SCHEMA).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        require(schema["properties"]["schema_version"]["const"] == "cash_institutional_flow_context_evidence.v1"
                and schema["properties"]["status"]["enum"] == ["complete", "unavailable", "source_failed", "binding_failed"], "evidence_schema_contract")
        for rel in MODULES:
            assert_networkless_source((ROOT / rel).read_text(encoding="utf-8"))
        from server.services.phase_i_i3_cash_institutional_flow_adapters import load_frozen_contract
        from server.services.phase_i_i3_cash_institutional_flow_offline_candidate import (
            CAPABILITY_ID, EVIDENCE_SCHEMA, EXECUTOR_ID, build_i3_candidate_runtime_adapter_registry,
        )
        require(CAPABILITY_ID == "cash_institutional_flow_context"
                and EXECUTOR_ID == "phase_i_i3_cash_institutional_flow_context_executor"
                and EVIDENCE_SCHEMA == "cash_institutional_flow_context_evidence.v1", "candidate_executor_identity")
        require(load_frozen_contract()["sources"] == a1.validate_contract(load_frozen_contract())["sources"], "frozen_mapping_authority")
        require(set(build_i3_candidate_runtime_adapter_registry()) == {(EXECUTOR_ID, "TWSE"), (EXECUTOR_ID, "TPEX")}, "isolated_candidate_registry")
        for rel in PROTECTED:
            require((ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", f"{BASELINE}:{rel}"], cwd=ROOT), f"production_drift:{rel}")
        for rel in ("schemas/unified_market_evidence_request.v3.schema.json", "schemas/unified_market_evidence_result.v3.schema.json",
                    "schemas/unified_market_evidence_audit_package.v3.schema.json"):
            require(b"cash_institutional_flow_context" not in (ROOT / rel).read_bytes(), f"public_v3_i3_exposure:{rel}")
        catalog = json.loads((ROOT / PROTECTED[0]).read_text(encoding="utf-8"))
        routing = json.loads((ROOT / PROTECTED[1]).read_text(encoding="utf-8"))
        require("cash_institutional_flow_context" not in json.dumps(catalog)
                and "cash_institutional_flow_context" not in json.dumps(routing), "i3_catalog_or_route_exposure")
        require(EXECUTOR_ID not in (ROOT / "scripts/m8r_06_03_production_adapter.py").read_text(encoding="utf-8")
                and EXECUTOR_ID not in (ROOT / "config/m8r_06_03_executor_registry_metadata.json").read_text(encoding="utf-8"), "i3_production_registry_import")
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        registry = build_production_runtime_adapter_registry()
        require(not registry.routes_for_executor(EXECUTOR_ID)
                and len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
                and len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1, "production_registry_routes")
        require(json.loads((ROOT / "docs/data_capabilities/phase_i_i1_source_authority.v1.json").read_text(encoding="utf-8"))["active_source_count"] == 3
                and json.loads((ROOT / "docs/data_capabilities/phase_i_i2_source_authority.v1.json").read_text(encoding="utf-8"))["active_source_count"] == 1
                and len(build_tool_specs()) == 6, "existing_runtime_or_mcp_drift")
        record = None
        if require_record:
            record = json.loads((ROOT / RECORD).read_text(encoding="utf-8"))
            require(record["schema_version"] == "phase_i_i3_a2_dormant_offline_implementation_candidate.v1"
                    and record["status"] == "DORMANT_IMPLEMENTATION_CANDIDATE_READY_FOR_REVIEW"
                    and record["owner_authority"] == OWNER and record["starting_main"] == BASELINE
                    and record["starting_head"] == START and record["starting_tree"] == START_TREE, "a2_governance_identity")
            require(record["a1_contract"]["path"] == a1.CONTRACT and record["a1_contract"]["sha256"] == a1.sha(ROOT / a1.CONTRACT), "a2_a1_provenance")
            technical = record["technical_implementation"]
            require(subprocess.check_output(["git", "rev-parse", technical["commit"] + "^{tree}"], cwd=ROOT).decode().strip() == technical["tree"], "technical_commit_tree")
            for rel in (*MODULES, SCHEMA, "tests/unit/test_phase_i_i3_a2_offline.py", "config/test_execution_profiles.json", "scripts/validate_phase_i_i3_a2_candidate.py"):
                require((ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", f"{technical['commit']}:{rel}"], cwd=ROOT), f"technical_bytes_changed:{rel}")
            require(technical["adapter_path"] == MODULES[0] and technical["candidate_executor_path"] == MODULES[1]
                    and technical["evidence_schema_path"] == SCHEMA
                    and technical["evidence_schema_sha256"] == sha(ROOT / SCHEMA), "technical_file_provenance")
            require(record["capability"] == {"capability_id": CAPABILITY_ID, "candidate_executor_id": EXECUTOR_ID,
                    "evidence_schema": EVIDENCE_SCHEMA}, "a2_capability_record")
            require(record["public_integration"] == {"catalog_present": False, "routing_present": False,
                    "request_v3_supported": False, "result_v3_projection": False, "audit_v3_reference": False}, "a2_public_boundary")
            require(record["runtime"] == {"production_registry_present": False, "runtime_executable": False,
                    "active_sources": 0, "production_routes": 0}, "a2_runtime_dormancy")
            require(record["offline"] == {"injected_input_only": True, "network_calls": 0,
                    "system_clock_reads": False, "raw_payload_persistence": False}, "a2_offline_boundary")
            require(record["batching"] == {"same_market_prepare_once": "PASS", "mixed_max_simulated_acquisitions": 2}, "a2_batching_proof")
            require(record["validation"]["A2_only"] == {"passed": 39, "skipped": 0, "deselected": 0}
                    and record["validation"]["I3_SSL_focused"] == {"passed": 255, "skipped": 0, "deselected": 0}
                    and record["validation"]["default_ci"] == {"passed": 1125, "skipped": 1, "deselected": 5}
                    and record["validation"]["full_current"] == {"passed": 1498, "skipped": 1, "deselected": 5}, "a2_validation_counts")
            require(record["not_proven_by_A2"] == ["live_HTTP_transport", "production_registry_wiring",
                    "public_V3_request_result_audit_integration", "source_activation", "route_activation", "merge"], "a2_unproven_boundary")
            require(record["A3_authorized"] is False and record["production_activation_authorized"] is False
                    and record["merge_authorized"] is False and record["A3_ready_for_separate_owner_decision"] is True, "a2_authorization_boundary")
    print("I3-A2 dormant offline candidate PASS; production/public routes absent; market GETs=0; MCP=6")
    return record


if __name__ == "__main__":
    validate(require_record="--technical-only" not in sys.argv)
