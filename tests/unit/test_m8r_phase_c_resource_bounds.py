import pytest
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan

PHASE_C_REGISTRY = {
    "schema_version": "m8_source_capability_registry.v1",
    "phase_c_activation_status": "conversation_driven_enabled_with_caveats",
    "active_runtime_source_families": ["TWSE_MIS", "TAIFEX_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"],
    "twse_mis_runtime_executable": True,
    "twse_openapi_runtime_executable": True,
    "tpex_openapi_runtime_executable": True,
    "m8_active_consolidated_status": {
        "twse_mis_runtime_executable": True,
        "twse_openapi_runtime_executable": True,
        "tpex_openapi_runtime_executable": True
    },
    "sources": [
        {"source_family": "TWSE_MIS", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TAIFEX_MIS", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TWSE_OPENAPI", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TPEX_OPENAPI", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"},
        {"source_family": "TAIFEX_OPENAPI", "runtime_available": True, "runtime_executable": True, "phase_c_activation_state": "enabled_one_shot"}
    ]
}

def make_req(request_id, target_ids, original_user_text="我的觀察清單現在怎麼樣？"):
    return {
      "clarification_reason": None,
      "clarification_required": False,
      "conversation_intent": {
        "clarification_reason": None,
        "clarification_required": False,
        "evidence_depth": "standard",
        "explicit_user_constraints": {},
        "inferred_defaults": {},
        "original_user_text": original_user_text,
        "schema_version": "m8r_ai_market_conversation_intent.v1",
        "scope_modes": ["watchlist"],
        "time_scope": {
          "explicit_range": None,
          "lookback_trading_days": None,
          "mode": "current"
        }
      },
      "dynamic_entity_requests": [],
      "execution_policy": {
        "network_allowed": False,
        "operator_confirmation_required": False,
        "polling": False,
        "scheduler": False
      },
      "explicit_user_constraints": {},
      "follow_up_context": None,
      "identity_resolver_output": {},
      "inferred_defaults": {},
      "market_context_requests": [],
      "optional_evidence": [],
      "original_user_text": original_user_text,
      "persistent_watchlist_reference": {
        "enabled_target_ids": target_ids,
        "source": "local_fixture",
        "watchlist_id": "wl-test"
      },
      "request_id": request_id,
      "required_evidence": [],
      "schema_version": "m8r_ai_evidence_request.v1",
      "useful_evidence": []
    }

def test_resource_bounds_limits():
    targets_10 = [f"TWSE:{2330+i}" for i in range(10)]
    plan = build_execution_plan(make_req("test-req-bounds", targets_10), bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    assert plan["execution_preview"]["expanded_scope"] is False
    assert plan["execution_preview"]["target_count"] == 10
    assert not any(i.get("blocking") for i in plan.get("issues", []))
    
    targets_11 = [f"TWSE:{2330+i}" for i in range(11)]
    plan = build_execution_plan(make_req("test-req-bounds", targets_11), bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    assert plan["execution_preview"]["expanded_scope"] is True
    assert plan["execution_preview"]["target_count"] == 11
    assert not any(i.get("blocking") for i in plan.get("issues", []))
    
    targets_50 = [f"TWSE:{2330+i}" for i in range(50)]
    plan = build_execution_plan(make_req("test-req-bounds", targets_50), bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    assert plan["execution_preview"]["expanded_scope"] is True
    assert plan["execution_preview"]["target_count"] == 50
    assert not any(i.get("blocking") for i in plan.get("issues", []))
    
    targets_51 = [f"TWSE:{2330+i}" for i in range(51)]
    plan = build_execution_plan(make_req("test-req-bounds", targets_51), bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    assert any(i["code"] == "rejected_resource_bound" and i["blocking"] for i in plan.get("issues", []))
