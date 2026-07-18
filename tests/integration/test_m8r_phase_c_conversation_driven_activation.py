import pytest
import json
import uuid
from pathlib import Path
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

def test_e2e_conversation_driven_one_shot_workflow(tmp_path):
    req = make_req("e2e-req-1", ["TWSE:2330", "TPEX:6488"])
    plan = build_execution_plan(req, bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    assert "execution_preview" in plan
    preview = plan["execution_preview"]
    assert preview["target_count"] == 2
    
    approval = {
        "schema_version": "m8r_phase_c_conversation_approval.v1",
        "approval_mode": "conversation_explicit_approval",
        "preview_id": preview["preview_id"],
        "request_id": req["request_id"],
        "approval_status": "approved",
        "approved_at_utc": "2026-07-18T13:00:00Z",
        "approved_text_summary": "就照這樣跑"
    }
    
    def dummy_twse_mis(target_ids, **kwargs):
        return {
            "targets": {
                "TWSE:2330": {
                    "TWSE_MIS": {"symbol": "2330", "market": "TWSE", "price": 1000.0, "retrieved_at": "2026-07-16T03:00:00Z"}
                }
            }
        }
        
    def dummy_eod(target_ids, **kwargs):
        return {
            "targets": {
                "TWSE:2330": {
                    "TWSE_OPENAPI": {"symbol": "2330", "market": "listed", "trade_date": "2026-07-17", "price": {"close": "1000.0"}, "activity": {"trade_volume": 100}, "retrieved_at_utc": "2026-07-18T03:00:00Z"}
                },
                "TPEX:6488": {
                    "TPEX_OPENAPI": {"symbol": "6488", "market": "tpex_otc", "trade_date": "2026-07-17", "price": {"close": "750.0"}, "activity": {"trade_volume": 50}, "retrieved_at_utc": "2026-07-18T03:00:00Z"}
                }
            }
        }
        
    res = execute_watchlist(
        req,
        mode="execute",
        bundle_type="snapshot",
        artifact_root=str(tmp_path),
        preview=preview,
        approval=approval,
        executors={
            "TWSE_MIS": dummy_twse_mis,
            "TWSE_OPENAPI": dummy_eod,
            "TPEX_OPENAPI": dummy_eod
        },
        source_capability_registry=PHASE_C_REGISTRY
    )
    
    assert res["status"] in ("success", "success_with_partial_coverage")
    assert res["observation_count"] > 0
    
    run_dir = tmp_path / res["run_id"]
    assert (run_dir / "execution_preview.json").exists()
    assert (run_dir / "approval_record.json").exists()
    assert (run_dir / "execution_result.json").exists()
    
    result_data = json.loads((run_dir / "execution_result.json").read_text(encoding="utf-8"))
    assert "execution_audit" in result_data
    audit = result_data["execution_audit"]
    assert audit["preview_id"] == preview["preview_id"]
    assert audit["approval_status"] == "approved"
    
    target_results = result_data["target_results"]
    tpex_res = [tr for tr in target_results if tr["target_id"] == "TPEX:6488" and tr.get("source_family") == "TPEX_OPENAPI"]
    assert len(tpex_res) == 1
    assert tpex_res[0]["fallback_used"] is True
    assert tpex_res[0]["requested_source_family"] == "TWSE_MIS"
    assert tpex_res[0]["actual_source_family"] == "TPEX_OPENAPI"
    assert tpex_res[0]["status"] == "fallback_success"
