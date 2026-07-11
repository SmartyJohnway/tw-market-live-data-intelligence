import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/M8_00_FINAL_ACCEPTANCE_AND_CLOSURE.md"
INVENTORY = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
PROFILE = ROOT / "config/test_execution_profiles.json"
M8_MODULES = [
    ROOT / "scripts/m8_source_freshness_evaluator.py",
    ROOT / "scripts/m8_multi_source_context_builder.py",
    ROOT / "scripts/m8_controlled_conversation_context.py",
]


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def _m8_inventory() -> dict:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return data["rich_observation_contract"]["m8_source_timing_authority_governance"]


def test_final_acceptance_doc_exists_and_contains_required_status():
    text = _doc_text()
    assert "m8_00_final_acceptance_pass_with_caveats" in text
    assert "M8-00 final acceptance: pass_with_caveats" in text
    assert "M8A-00-OFFICIAL-EOD-ADAPTER-SCOPE-AND-CONTRACT-PREFLIGHT" in text


def test_final_doc_lists_accepted_tasks():
    text = _doc_text()
    for task in [f"M8-00-0{i}" for i in range(9)]:
        assert task in text


def test_final_doc_lists_accepted_artifacts():
    text = _doc_text()
    for artifact in [
        "M8_SOURCE_TIMING_AUTHORITY_GOVERNANCE_PREFLIGHT.md",
        "M8_SOURCE_CAPABILITY_REGISTRY_SCHEMA.md",
        "m8_source_capability_registry.json",
        "M8_FRESHNESS_TIMESTAMP_DELAY_SEMANTICS.md",
        "M8_MULTI_SOURCE_MARKET_CONTEXT_SCHEMA.md",
        "M8_SOURCE_FRESHNESS_EVALUATOR.md",
        "m8_source_freshness_evaluator.py",
        "M8_MULTI_SOURCE_CONTEXT_BUILDER.md",
        "m8_multi_source_context_builder.py",
        "M8_CONTROLLED_CONVERSATION_CONTEXT_INTEGRATION.md",
        "m8_controlled_conversation_context.py",
        "M8_COMPATIBILITY_HARDENING.md",
    ]:
        assert artifact in text


def test_source_family_final_status():
    text = _doc_text()
    for phrase in [
        "TWSE_MIS",
        "TAIFEX_MIS",
        "TWSE_OPENAPI",
        "TPEX_OPENAPI",
        "TAIFEX_OPENAPI",
        "MOPS",
        "MANUAL_OPERATOR_EVIDENCE",
        "EXTERNAL_VALIDATION_ONLY",
        "CREDENTIAL_GATED_PROVIDER",
        "TPEX_MIS not introduced",
        "rotc_ not introduced",
        "TAIFEX_MIS execution not introduced",
        "OpenAPI adapters not introduced",
    ]:
        assert phrase in text


def test_interpretation_principle_recorded():
    text = _doc_text()
    for phrase in [
        "source-context and AI-readability foundation",
        "not an AI response policy engine",
        "downstream AI output depends on model behavior, system prompts, user prompts, agent policies, and product-layer controls",
        "avoid over-broad, brittle forbidden-word expansion",
        "faithful, source-aware, caveated, safe-projected context",
    ]:
        assert phrase in text


def test_inventory_final_acceptance():
    meta = _m8_inventory()
    assert meta["status"] == "m8_00_final_acceptance_pass_with_caveats"
    assert meta["completed_tasks"] == [f"M8-00-0{i}" for i in range(9)]
    assert (ROOT / meta["final_acceptance_doc"]).exists()
    assert meta["final_acceptance_status"] == "pass_with_caveats"
    for flag in [
        "m8_00_final_accepted",
        "source_governance_final_accepted",
        "source_registry_final_accepted",
        "freshness_semantics_final_accepted",
        "freshness_evaluator_final_accepted",
        "multi_source_context_builder_final_accepted",
        "controlled_conversation_context_projection_final_accepted",
        "compatibility_hardening_final_accepted",
        "m8_00_is_source_context_foundation_not_ai_response_policy_engine",
        "overbroad_forbidden_word_expansion_discouraged",
        "downstream_ai_output_depends_on_model_prompt_and_agent_policy",
        "project_responsibility_is_safe_source_context_projection",
    ]:
        assert meta[flag] is True
    assert meta["next_task"] == "M8A-00-OFFICIAL-EOD-ADAPTER-SCOPE-AND-CONTRACT-PREFLIGHT"


def test_boundary_flags_remain_closed():
    meta = _m8_inventory()
    assert meta["no_m8a_started"] is True
    for flag in [
        "twse_openapi_adapter_added",
        "tpex_openapi_adapter_added",
        "taifex_openapi_adapter_added",
        "taifex_mis_execution_added",
        "tpex_mis_introduced",
        "rotc_route_introduced",
        "emerging_stock_live_supported",
        "network_fetch_added",
        "runtime_behavior_changed",
        "frontend_changed",
        "server_changed",
        "mcp_changed",
        "ai_model_call_added",
        "db_write_added",
        "scheduler_added",
        "polling_added",
        "hidden_fetch_added",
        "startup_fetch_added",
        "mode_d_added",
        "level_3_added",
        "m5f_mutated",
        "level1_mutated",
        "raw_payload_exposure_allowed",
    ]:
        assert meta[flag] is False


def test_m8_modules_still_import_safe():
    forbidden_roots = {
        "requests", "urllib", "httpx", "aiohttp", "socket", "server", "frontend",
        "openai", "mcp", "fastapi", "uvicorn",
    }
    for module in M8_MODULES:
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            assert forbidden_roots.isdisjoint(names), f"{module} imports forbidden module roots {names}"


def test_default_ci_includes_m8_final_acceptance_test():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    paths = data["profiles"]["default-ci"]["pytest_paths"]
    assert "tests/unit/test_m8_00_final_acceptance.py" in paths
