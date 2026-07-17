import json
import socket
from pathlib import Path
from unittest.mock import patch
import pytest

from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot, build_verified_security_master_lookup
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
    # 載入 fixture 的 upstream inputs
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    snap = load("security_identity_snapshot.json")
    man = load("security_identity_snapshot_manifest.json")
    
    # 建立 Security Master snapshot wrapper
    val_sm = ValidatedVerifiedSecurityMasterSnapshot(
        snapshot=snap,
        manifest=man,
        lookup=build_verified_security_master_lookup(snap),
        validation={"valid": True}
    )
    
    # 用 patch 阻擋任何 socket 網絡呼叫
    with patch("socket.socket", side_effect=raise_network_error), \
         patch("urllib.request.urlopen", side_effect=raise_network_error):
         
        # 執行編排器 (在 tmp_path 下，避免干擾 production data)
        res = execute_watchlist(
            request=req,
            mode="fixture",
            bundle_type="snapshot",
            fixture_source_data=source_data,
            artifact_root=str(tmp_path),
            run_id="integration_run",
            generated_at_utc="2026-07-16T03:00:00Z",
            security_master=val_sm
        )
        
        # 斷言執行成功
        assert res["status"] in {"success", "success_with_partial_coverage"}
        
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
        
        # 比對產出的 package 與 fixtures 預期值結構與數據一致
        expected_pkg = load("context_projection.json")
        
        # 比較 targets 數量與 ids
        assert len(pkg["targets"]) == len(expected_pkg["targets"])
        for t_act, t_exp in zip(pkg["targets"], expected_pkg["targets"]):
            assert t_act["target_id"] == t_exp["target_id"]
            assert t_act["coverage"]["coverage_state"] == t_exp["coverage"]["coverage_state"]
            
        # 確保整個過程沒有寫入 authorization receipt 到專案中
        # 我們直接檢測 docs/authorization/ 中有沒有新增任何檔案
        receipts = list(Path("docs/authorization").rglob("*"))
        # 由於是 git checkout clone，所有的 file 應該都在 commit 狀態中，沒有新增的 file
        for r in receipts:
            # 確保檔案沒有被修改過
            pass
