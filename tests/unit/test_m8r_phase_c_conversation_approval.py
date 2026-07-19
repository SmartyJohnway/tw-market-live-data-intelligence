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
        "network_allowed": True,
        "operator_confirmation_required": False,
        "polling": False,
        "scheduler": False,
        "execution_profile": "phase_c_conversation_driven_one_shot.v1"
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

def test_conversation_approval_validation(tmp_path):
    req = make_req("test-req-approval", ["TWSE:2330"])
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
    
    # 1. 無 approval 執行 -> 拒絕
    res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path), preview=preview, approval=None, source_capability_registry=PHASE_C_REGISTRY)
    assert res["status"] == "authorization_failed"
    assert any(issue["code"] == "approval_missing" for issue in res["issues"])
    
    # 2. 正常 approval 執行 -> 成功
    def dummy_mis(targets, **kwargs):
        return {"targets": {"TWSE:2330": {"TWSE_MIS": {"symbol": "2330", "market": "TWSE", "price": 1000.0, "retrieved_at": "2026-07-16T03:00:00Z"}}}}
    def dummy_eod(targets, **kwargs):
        return {"targets": {"TWSE:2330": {"TWSE_OPENAPI": {"symbol": "2330", "market": "listed", "trade_date": "2026-07-15", "price": {"close": "1000.0"}, "activity": {"trade_volume": 100}, "retrieved_at_utc": "2026-07-16T03:00:00Z"}}}}
    
    res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path), preview=preview, approval=valid_approval, executors={"TWSE_MIS": dummy_mis, "TWSE_OPENAPI": dummy_eod}, source_capability_registry=PHASE_C_REGISTRY)
    assert res["status"] in ("success", "success_with_partial_coverage")
    
    # 3. 關聯到不同 preview_id 的 approval -> 拒絕
    bad_approval = valid_approval.copy()
    bad_approval["preview_id"] = "preview-bad1234"
    res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path/'other'), preview=preview, approval=bad_approval, executors={"TWSE_MIS": dummy_mis}, source_capability_registry=PHASE_C_REGISTRY)
    assert res["status"] == "authorization_failed"
    assert any(issue["code"] == "approval_referenced_different_preview" for issue in res["issues"])

    # 4. Replay 驗證 -> 再次使用同一個 preview_id + request_id 執行 -> 拒絕
    res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path/'other_replay'), preview=preview, approval=valid_approval, executors={"TWSE_MIS": dummy_mis, "TWSE_OPENAPI": dummy_eod}, source_capability_registry=PHASE_C_REGISTRY)
    assert res["status"] == "authorization_failed"
    assert any(issue["code"] == "authorization_replayed" for issue in res["issues"])

def test_conversation_approval_metadata_tampering(tmp_path):
    req = make_req("test-req-tamper", ["TWSE:2330"])
    plan = build_execution_plan(req, bundle_type="snapshot", source_capability_registry=PHASE_C_REGISTRY)
    canonical_preview = plan["execution_preview"]
    
    # 建立一個標準的驗證 approval record
    def get_approval(prev_id):
        return {
            "schema_version": "m8r_phase_c_conversation_approval.v1",
            "approval_mode": "conversation_explicit_approval",
            "preview_id": prev_id,
            "request_id": req["request_id"],
            "approval_status": "approved",
            "approved_at_utc": "2026-07-18T12:00:00Z",
            "approved_text_summary": "同意執行"
        }
        
    fields_to_tamper = [
        ("artifact_retention_days", 999),
        ("fallback_policy", "lenient_bypass"),
        ("partial_success_policy", "strict_all_or_nothing"),
        ("estimated_network_calls", 5000),
        ("expanded_scope", True),
        ("request_summary", "Modified summary to leak credentials"),
        ("target_count", 99)
    ]
    
    for field, val in fields_to_tamper:
        tampered_preview = canonical_preview.copy()
        tampered_preview[field] = val
        
        # 情況 A：篡改了內容，但保留了原始的 preview_id (希望能騙過 hash 校驗)
        res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path/f"tamper-A-{field}"), preview=tampered_preview, approval=get_approval(canonical_preview["preview_id"]), source_capability_registry=PHASE_C_REGISTRY)
        assert res["status"] == "authorization_failed", f"Failed closed expectation failed for field: {field} (tamper A)"
        assert any(issue["code"] == "preview_plan_mismatch" for issue in res["issues"])
        
        # 情況 B：篡改了內容，並偽造了對應內容的新 preview_id，試圖讓兩者相符，但這不等於 canonical preview_id
        # 我們重新算一下這個偽造 preview 的 expected_id
        from scripts.m8r_03d_watchlist_controlled_executor import sha256_json
        fake_body = {k: v for k, v in tampered_preview.items() if k != "preview_id"}
        fake_id = "preview-" + sha256_json(fake_body)
        tampered_preview["preview_id"] = fake_id
        
        res = execute_watchlist(req, mode="execute", bundle_type="snapshot", artifact_root=str(tmp_path/f"tamper-B-{field}"), preview=tampered_preview, approval=get_approval(fake_id), source_capability_registry=PHASE_C_REGISTRY)
        assert res["status"] == "authorization_failed", f"Failed closed expectation failed for field: {field} (tamper B)"
        assert any(issue["code"] == "preview_plan_mismatch" for issue in res["issues"])

