import json
import uuid
from pathlib import Path
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist, SOURCE_ADAPTERS, NORMALIZERS
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot

def test_pre_registered_source_activates_without_core_routing_changes():
    # 驗證「registry-driven activation of pre-registered adapters」：
    # 只需在 capability registry 中宣告並設定一個 pre-registered source family，
    # 即可透過 Phase C 的動態路由機制完成來源選擇、呼叫與歸一化，
    # 不需要修改 planner/executor 的核心路由邏輯。
    # 注意：新 source 仍然需要 adapter + normalizer + bundle role implementation，
    # 這些必須在整合前完成 plugin 預先註冊。
    # 建立測試用 Mock Registry，宣告支援 FIXTURE_TEST_SOURCE
    registry = {
      "schema_version": "m8_source_capability_registry.v1",
      "phase_c_activation_status": "conversation_driven_enabled_with_caveats",
      "active_runtime_source_families": [
        "FIXTURE_TEST_SOURCE"
      ],
      "sources": [
        {
          "source_family": "FIXTURE_TEST_SOURCE",
          "timing_class": "liveish_intraday_snapshot",
          "runtime_executable": True,
          "phase_c_activation_state": "enabled_one_shot",
          "market_scope": {
            "TWSE": "listed"
          }
        }
      ]
    }

    called_adapter = False
    called_normalizer = False

    def mock_adapter(plan, request, g):
        nonlocal called_adapter
        called_adapter = True
        return {
            "targets": {
                "TWSE:2330": {
                    "FIXTURE_TEST_SOURCE": {"symbol": "2330", "price": 100.0}
                }
            }
        }

    def mock_normalizer(row, target, reference_clock_utc):
        nonlocal called_normalizer
        called_normalizer = True
        return {
            "schema_version": "m8r_watchlist_input_observation.v1",
            "target_id": target["target_id"],
            "source_family": "FIXTURE_TEST_SOURCE",
            "timing_class": "liveish_intraday_snapshot",
            "context_type": "liveish_observation",
            "retrieved_at_utc": reference_clock_utc,
            "requested_identity": {},
            "resolved_identity": {},
            "currentness": {},
            "facts": {
                "symbol": "2330",
                "price": 100.0
            },
            "issues": []
        }

    # Pre-register the plugin adapter/normalizer/role before execution.
    # This simulates the integration step required for any new source:
    # adapter (how to fetch) + normalizer (how to standardize) + bundle role (how to bundle)
    # are all pre-registered here, then activated purely through the capability registry.
    from scripts.m8r_03c_watchlist_bundle_builder import SOURCE_ROLE_MATRIX
    SOURCE_ROLE_MATRIX["FIXTURE_TEST_SOURCE"] = {
        'role': 'current',
        'timing_classes': {'liveish_intraday_snapshot'},
        'context_types': {'liveish_observation'}
    }
    SOURCE_ADAPTERS["FIXTURE_TEST_SOURCE"] = mock_adapter
    NORMALIZERS["FIXTURE_TEST_SOURCE"] = mock_normalizer

    req_id = f"req-zero-code-{uuid.uuid4()}"

    try:
        request = {
            "schema_version": "m8r_ai_evidence_request.v1",
            "request_id": req_id,
            "original_user_text": "testing zero-code expansion",
            "dynamic_entity_requests": [],
            "market_context_requests": [],
            "required_evidence": [
                {
                    "capability_id": "fixture_test_listed_liveish",
                    "fallback_behavior": "record_missing",
                    "preferred_timing_class": "liveish_intraday_snapshot",
                    "priority": "required",
                    "required_for_answer": True,
                    "source_family_preference": [
                        "FIXTURE_TEST_SOURCE"
                    ],
                    "time_scope": {
                        "explicit_range": None,
                        "lookback_trading_days": None,
                        "mode": "current"
                    }
                }
            ],
            "useful_evidence": [],
            "optional_evidence": [],
            "persistent_watchlist_reference": {
                "watchlist_id": "wl-test",
                "source": "local_fixture",
                "enabled_target_ids": ["TWSE:2330"]
            },
            "execution_policy": {
                "network_allowed": True,
                "operator_confirmation_required": False,
                "polling": False,
                "scheduler": False,
                "execution_profile": "phase_c_conversation_driven_one_shot.v1"
            },
            "conversation_intent": {
                "schema_version": "m8r_ai_market_conversation_intent.v1",
                "original_user_text": "testing zero-code expansion",
                "scope_modes": ["watchlist"],
                "time_scope": {"mode": "current_plus_recent", "lookback_trading_days": 20, "explicit_range": None},
                "evidence_depth": "standard",
                "explicit_user_constraints": {},
                "inferred_defaults": {},
                "clarification_required": False,
                "clarification_reason": None
            },
            "explicit_user_constraints": {},
            "inferred_defaults": {},
            "clarification_required": False,
            "clarification_reason": None,
            "identity_resolver_output": {},
            "follow_up_context": None
        }

        # 載入實體 Verified Security Master
        security_master = load_verified_security_master_snapshot(
            "tests/fixtures/m8r_03e_r5a/security_identity_snapshot.json",
            "tests/fixtures/m8r_03e_r5a/security_identity_snapshot_manifest.json",
            allow_fixture_snapshot=True
        )

        # 1. 規劃階段，應正確規劃自定義來源
        plan = build_execution_plan(
            request, 
            bundle_type="snapshot",
            security_master=security_master,
            source_capability_registry=registry,
            allow_fixture_snapshot=True
        )

        assert "execution_preview" in plan
        preview = plan["execution_preview"]
        assert preview["preview_id"].startswith("preview-")
        assert "FIXTURE_TEST_SOURCE" in preview["planned_sources"]

        approval = {
            "schema_version": "m8r_phase_c_conversation_approval.v1",
            "approval_mode": "conversation_explicit_approval",
            "preview_id": preview["preview_id"],
            "request_id": request["request_id"],
            "approval_status": "approved",
            "approved_at_utc": "2026-07-18T12:05:00Z",
            "approved_text_summary": "執行"
        }

        # 2. 執行階段，應動態 dispatch 到我們的 Mock 執行器與歸一化器
        res = execute_watchlist(
            request,
            mode="execute",
            bundle_type="snapshot",
            preview=preview,
            approval=approval,
            security_master=security_master,
            source_capability_registry=registry,
            artifact_root="artifacts/zero_code_test"
        )

        # 驗證結果
        print("ZERO_CODE_TEST RES:", res)
        assert res["status"] in ("success", "success_with_partial_coverage")
        assert called_adapter is True
        assert called_normalizer is True
        assert res["observation_count"] == 1

        # 驗證審計日誌中正確綁定 Operation ID，且無硬編碼反推
        audit = res["execution_audit"]
        assert "op-TWSE:2330-FIXTURE_TEST_SOURCE" in audit["planned_operation_ids"]
        assert "op-TWSE:2330-FIXTURE_TEST_SOURCE" in audit["actual_operation_ids"]

    finally:
        from scripts.m8r_03c_watchlist_bundle_builder import SOURCE_ROLE_MATRIX
        SOURCE_ROLE_MATRIX.pop("FIXTURE_TEST_SOURCE", None)
        SOURCE_ADAPTERS.pop("FIXTURE_TEST_SOURCE", None)
        NORMALIZERS.pop("FIXTURE_TEST_SOURCE", None)
        # 清除本測試在 artifacts 中產生的 claim 檔案以防止殘留影響其它執行
        consumption_dir = Path("artifacts/m8r_03d_authorization_consumption")
        if consumption_dir.exists():
            for p in consumption_dir.glob("*.json"):
                try:
                    content = p.read_text(encoding="utf-8")
                    if req_id in content:
                        p.unlink()
                except Exception:
                    pass
