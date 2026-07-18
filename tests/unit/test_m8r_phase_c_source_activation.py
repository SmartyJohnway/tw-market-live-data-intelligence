import pytest
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan

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
        "network_allowed": True,
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
      "required_evidence": [
        {
          "capability_id": "twse_mis_listed_liveish",
          "fallback_behavior": "record_missing",
          "preferred_timing_class": "liveish_intraday_snapshot",
          "priority": "required",
          "required_for_answer": True,
          "source_family_preference": [
            "TWSE_MIS"
          ],
          "time_scope": {
            "explicit_range": None,
            "lookback_trading_days": None,
            "mode": "current"
          }
        }
      ],
      "schema_version": "m8r_ai_evidence_request.v1",
      "useful_evidence": []
    }

def test_source_activation_policy_states():
    req = make_req("test-req-sources", ["TWSE:2330"])
    
    registry = {
        "schema_version": "m8_source_capability_registry.v1",
        "phase_c_activation_status": "conversation_driven_enabled_with_caveats",
        "active_runtime_source_families": ["TWSE_MIS", "TWSE_OPENAPI"],
        "twse_mis_runtime_executable": True,
        "twse_openapi_runtime_executable": True,
        "m8_active_consolidated_status": {
            "twse_mis_runtime_executable": True,
            "twse_openapi_runtime_executable": True
        },
        "sources": [
            {
                "source_family": "TWSE_MIS",
                "runtime_available": True,
                "runtime_executable": True,
                "phase_c_activation_state": "enabled_one_shot"
            },
            {
                "source_family": "TWSE_OPENAPI",
                "runtime_available": True,
                "runtime_executable": True,
                "phase_c_activation_state": "validated_not_activated"
            }
        ]
    }
    
    plan = build_execution_plan(req, bundle_type="snapshot", source_capability_registry=registry)
    
    target = plan["targets"][0]
    assert target["current_source_plan"] is not None
    assert target["current_source_plan"]["source_family"] == "TWSE_MIS"
    assert target["eod_source_plan"] == {}
