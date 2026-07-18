import pytest
import uuid
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
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

def make_req(request_id_prefix, target_ids, original_user_text="我的觀察清單現在怎麼樣？"):
    request_id = f"{request_id_prefix}-{uuid.uuid4()}"
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

def test_retention_policy_metadata(tmp_path):
    req = make_req("test-req-retention", ["TWSE:2330"])
    plan = build_execution_plan(req, bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    preview = plan["execution_preview"]
    
    valid_approval = {
        "schema_version": "m8r_phase_c_conversation_approval.v1",
        "approval_mode": "conversation_explicit_approval",
        "preview_id": preview["preview_id"],
        "request_id": req["request_id"],
        "approval_status": "approved",
        "approved_at_utc": "2026-07-18T12:00:00Z",
        "approved_text_summary": "執行"
    }
    
    def dummy_mis(targets, **kwargs):
        return {"targets": {"TWSE:2330": {"TWSE_MIS": {"symbol": "2330", "market": "TWSE", "price": 1000.0, "retrieved_at": "2026-07-16T03:00:00Z"}}}}
    def dummy_eod(targets, **kwargs):
        return {"targets": {"TWSE:2330": {"TWSE_OPENAPI": {"symbol": "2330", "market": "listed", "trade_date": "2026-07-15", "price": {"close": "1000.0"}, "activity": {"trade_volume": 100}, "retrieved_at_utc": "2026-07-16T03:00:00Z"}}}}
        
    res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path), preview=preview, approval=valid_approval, executors={"TWSE_MIS": dummy_mis, "TWSE_OPENAPI": dummy_eod}, source_capability_registry=PHASE_C_REGISTRY)
    
    assert "retention_policy" in res
    policy = res["retention_policy"]
    assert policy["default_retention_days"] == 30
    assert policy["manual_pin_supported"] is True
    assert policy["manual_delete_supported"] is True
    assert policy["expired_artifact_behavior"] == "eligible_for_cleanup"
