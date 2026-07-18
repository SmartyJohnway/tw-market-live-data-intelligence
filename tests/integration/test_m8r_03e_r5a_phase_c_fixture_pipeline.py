import json
import socket
import copy
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

class BlockedNetworkError(RuntimeError):
    pass

def raise_network_error(*args, **kwargs):
    raise BlockedNetworkError("Network access is strictly forbidden in Phase C offline modes.")

def test_integration_phase_c_fixture_pipeline(tmp_path):
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    cap_registry = load("source_capability_snapshot.json")
    
    val_sm = load_verified_security_master_snapshot(
        str(FIX_DIR / "security_identity_snapshot.json"),
        str(FIX_DIR / "security_identity_snapshot_manifest.json"),
        allow_fixture_snapshot=True
    )
    
    # 建立 spies 監視 authorization consume 與 receipt 寫入行為
    import scripts.m8r_03d_watchlist_controlled_executor as executor_module
    import scripts.m8r_filesystem_safety as fs_safety_module
    
    spy_claim = MagicMock(wraps=executor_module._claim_authorization)
    spy_create = MagicMock(wraps=fs_safety_module.atomic_create_text_exclusive)
    
    with patch("socket.socket", side_effect=raise_network_error), \
         patch("urllib.request.urlopen", side_effect=raise_network_error), \
         patch.object(executor_module, "_claim_authorization", spy_claim), \
         patch.object(fs_safety_module, "atomic_create_text_exclusive", spy_create):
         
        # 執行編排器
        res = execute_watchlist(
            request=req,
            mode="fixture",
            bundle_type="snapshot",
            fixture_source_data=source_data,
            artifact_root=str(tmp_path),
            run_id="integration_run",
            generated_at_utc="2026-07-16T03:00:00Z",
            security_master=val_sm,
            source_capability_registry=cap_registry
        )
        
        assert res["status"] in {"success", "success_with_partial_coverage"}
        
        # 實質斷言：沒有進行任何憑證消耗（call_count == 0）且無 receipt 寫入
        assert spy_claim.call_count == 0, "Authorization claim was unexpectedly invoked"
        assert spy_create.call_count == 0, "Receipt file write was unexpectedly invoked"
        
        # 載入生成的 plan, result 和 bundle
        run_dir = tmp_path / "integration_run"
        plan = json.loads((run_dir / "execution_plan.json").read_text(encoding="utf-8"))
        bundle = json.loads((run_dir / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
        
        # 使用 builder 產生 package
        pkg = build_watchlist_ai_context_package(
            validated_request=req,
            execution_plan=plan,
            execution_result=res,
            watchlist_bundle=bundle,
            generated_at_utc="2026-07-16T03:00:00Z"
        )
        
        # 驗證 package
        manifest_upstream = {
            "validated_request": req,
            "execution_plan": plan,
            "execution_result": res,
            "watchlist_bundle": bundle
        }
        val_pkg = validate_watchlist_ai_context_package(pkg, upstream_artifacts=manifest_upstream)
        assert val_pkg["valid"], f"Generated package is invalid: {val_pkg['issues']}"

def test_capability_snapshot_consumption_and_unsupported_filtering(tmp_path):
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    cap_registry = load("source_capability_snapshot.json")
    
    val_sm = load_verified_security_master_snapshot(
        str(FIX_DIR / "security_identity_snapshot.json"),
        str(FIX_DIR / "security_identity_snapshot_manifest.json"),
        allow_fixture_snapshot=True
    )
    
    # 建立一個篡改的 capability registry，將 twse_mis 標記為不可執行 (runtime_executable=False)
    tampered_registry = copy.deepcopy(cap_registry)
    tampered_registry["twse_mis_runtime_executable"] = False
    
    # 執行 watchlist
    res = execute_watchlist(
        request=req,
        mode="fixture",
        bundle_type="snapshot",
        fixture_source_data=source_data,
        artifact_root=str(tmp_path),
        run_id="cap_neg_run",
        generated_at_utc="2026-07-16T03:00:00Z",
        security_master=val_sm,
        source_capability_registry=tampered_registry
    )
    
    # 驗證：由於 TWSE_MIS 被 capability registry 阻擋，TWSE:2330 規劃出的 current_source_plan 必須為空 (拒絕路由)
    run_dir = tmp_path / "cap_neg_run"
    plan = json.loads((run_dir / "execution_plan.json").read_text(encoding="utf-8"))
    t_map = {t["target_id"]: t for t in plan["targets"]}
    assert t_map["TWSE:2330"]["current_source_plan"] == {}
    # 且其 expected_coverage 應降級為 partial (因為還有 EOD 依然可用)
    assert t_map["TWSE:2330"]["expected_coverage"] == "partial"
    
    # 模擬 unsupported source family 拒絕
    unsupported_registry = copy.deepcopy(cap_registry)
    # 將 TWSE_OPENAPI 自 active_runtime_source_families 中移除，模擬不支持
    unsupported_registry["active_runtime_source_families"] = ["TWSE_MIS", "TPEX_OPENAPI"]
    
    res2 = execute_watchlist(
        request=req,
        mode="fixture",
        bundle_type="snapshot",
        fixture_source_data=source_data,
        artifact_root=str(tmp_path),
        run_id="cap_unsupported_run",
        generated_at_utc="2026-07-16T03:00:00Z",
        security_master=val_sm,
        source_capability_registry=unsupported_registry
    )
    
    run_dir2 = tmp_path / "cap_unsupported_run"
    plan2 = json.loads((run_dir2 / "execution_plan.json").read_text(encoding="utf-8"))
    t_map2 = {t["target_id"]: t for t in plan2["targets"]}
    
    # 驗證：由於 TWSE_OPENAPI 移出 active 列表，TWSE:2330 規劃出的 eod_source_plan 必須為空 (拒絕路由)
    assert t_map2["TWSE:2330"]["eod_source_plan"] == {}
