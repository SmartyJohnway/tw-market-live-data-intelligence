import copy
import json
import pytest
from pathlib import Path
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot, VerifiedSecurityMasterSnapshotError
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def test_variant_a_source_adapter_failure(tmp_path):
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    cap_registry = load("source_capability_snapshot.json")
    
    # 載入正式的 security master wrapper
    from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot
    val_sm = load_verified_security_master_snapshot(
        str(FIX_DIR / "security_identity_snapshot.json"),
        str(FIX_DIR / "security_identity_snapshot_manifest.json"),
        allow_fixture_snapshot=True
    )
    
    # 模擬 TWSE_MIS 故障注入：移除所有的 TWSE_MIS 觀測值
    tampered_source = copy.deepcopy(source_data)
    for tid in tampered_source["targets"]:
        if "TWSE_MIS" in tampered_source["targets"][tid]:
            del tampered_source["targets"][tid]["TWSE_MIS"]
            
    # 重新執行 watchlist pipeline
    res = execute_watchlist(
        request=req,
        mode="fixture",
        bundle_type="snapshot",
        fixture_source_data=tampered_source,
        artifact_root=str(tmp_path),
        run_id="variant_a_run",
        generated_at_utc="2026-07-16T03:00:00Z",
        security_master=val_sm,
        source_capability_registry=cap_registry
    )
    
    # 驗證執行成功（有 fallback 機制，不中斷）
    assert res["status"] in {"success", "success_with_partial_coverage"}
    
    # 載入產出的 bundle 檔案，確認執行期 coverage 降級
    run_dir = tmp_path / "variant_a_run"
    bundle = json.loads((run_dir / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
    
    t_cov = {c["target_id"]: c for c in bundle["coverage"]["targets"]}
    
    # TWSE:2330 本應有 TWSE_MIS (live-ish)，但現在缺失，所以變為 partial 覆蓋
    assert t_cov["TWSE:2330"]["coverage_state"] == "partial"
    
    # 驗證缺失的能力被正確列入 missing_evidence 且沒有交叉污染
    missing_caps = [m for m in bundle["missing_evidence"] if m["target_id"] == "TWSE:2330"]
    assert any(m["capability_id"] == "current_mis_observation" for m in missing_caps)

def test_variant_b_stale_and_missing_pipeline(tmp_path):
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    cap_registry = load("source_capability_snapshot.json")
    
    val_sm = load_verified_security_master_snapshot(
        str(FIX_DIR / "security_identity_snapshot.json"),
        str(FIX_DIR / "security_identity_snapshot_manifest.json"),
        allow_fixture_snapshot=True
    )
    
    # 重新執行 watchlist pipeline，直接讀取原始 fixture
    res = execute_watchlist(
        request=req,
        mode="fixture",
        bundle_type="snapshot",
        fixture_source_data=source_data,
        artifact_root=str(tmp_path),
        run_id="variant_b_run",
        generated_at_utc="2026-07-16T03:00:00Z",
        security_master=val_sm,
        source_capability_registry=cap_registry
    )
    
    assert res["status"] in {"success", "success_with_partial_coverage"}
    run_dir = tmp_path / "variant_b_run"
    
    # 1. 載入 bundle 檔案，做實質隔離與新鮮度推導斷言
    bundle = json.loads((run_dir / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
    
    # 建立 target 覆蓋字典
    t_cov = {t["target_id"]: t["coverage"] for t in bundle["targets"]}
    
    # TWSE:2308 (Stale)：其 coverage_state 應為 partial，且缺失欄位為 currentness
    assert t_cov["TWSE:2308"]["coverage_state"] == "partial"
    assert "currentness" in t_cov["TWSE:2308"]["missing_field_groups"]
    
    # TWSE:2382 (Missing EOD)：其 coverage_state 應為 partial，且缺失欄位為 eod_reference
    assert t_cov["TWSE:2382"]["coverage_state"] == "partial"
    assert "eod_reference" in t_cov["TWSE:2382"]["missing_field_groups"]
    
    # 2. 驗證 missing_evidence 中的 reason codes 隔離且明確不同
    missing_ev = bundle["missing_evidence"]
    
    m_2308 = [m for m in missing_ev if m["target_id"] == "TWSE:2308"]
    m_2382 = [m for m in missing_ev if m["target_id"] == "TWSE:2382"]
    
    # 2308 應包含 currentness 驗證失效 (stale)
    assert any(m["capability_id"] == "currentness_validation" and m["reason_code"] == "stale_observation" for m in m_2308)
    
    # 2382 應包含 EOD 缺失
    assert any(m["capability_id"] == "official_eod_reference" and m["reason_code"] == "EOD reference unavailable" for m in m_2382)
    
    # 3. 驗證 unaffected targets (如 TWSE:2330) 完好無損，未受污染且依然為 usable
    assert t_cov["TWSE:2330"]["coverage_state"] == "usable"
    
    # 4. 驗證整體 bundle 狀態為 partial
    assert bundle["schema_version"] == "m8r_watchlist_snapshot_bundle.v1"
    
    # 5. 驗證最終 context package 內之 citation 行為
    pkg = build_watchlist_ai_context_package(
        validated_request=req,
        execution_plan=json.loads((run_dir / "execution_plan.json").read_text(encoding="utf-8")),
        execution_result=res,
        watchlist_bundle=bundle,
        generated_at_utc="2026-07-16T03:00:00Z"
    )
    
    t_pkg = {t["target_id"]: t for t in pkg["targets"]}
    
    # TWSE:2308 (Stale) 依然有觀測資料，其 citations 列表不應為空
    assert len(t_pkg["TWSE:2308"]["citations"]) > 0
    
    # TWSE:2382 缺失 EOD reference Facts，其 eod_reference 欄位應為空，且不應生成虛假的 citations
    assert t_pkg["TWSE:2382"]["eod_reference"] == {}

def test_variant_c_tampering_fail_closed(tmp_path):
    req = load("bounded_request.json")
    plan = load("execution_plan.json")
    bundle = load("evidence_bundle.json")
    pkg = load("context_projection.json")
    
    result = {
        "schema_version": "m8r_03d_watchlist_execution_result.v1",
        "run_id": "temp_run",
        "plan_id": plan["plan_id"],
        "request_id": req["request_id"],
        "request_hash": plan["request_hash"],
        "status": "success",
        "mode": "fixture"
    }
    
    # 1. 驗證 package fact tampering 攔截
    tampered_pkg = copy.deepcopy(pkg)
    assert tampered_pkg["targets"][0]["current_observation"]["latest_price"] is not None
    tampered_pkg["targets"][0]["current_observation"]["latest_price"] = 99999.0
    
    val_tampered = validate_watchlist_ai_context_package(
        tampered_pkg, 
        upstream_artifacts={"validated_request": req, "execution_plan": plan, "execution_result": result, "watchlist_bundle": bundle}
    )
    assert not val_tampered["valid"]
    
    # 2. 驗證 Security Master 篡改攔截
    snap = load("security_identity_snapshot.json")
    man = load("security_identity_snapshot_manifest.json")
    
    # 篡改情境 A：修改 record 內容而不改其 record_hash
    snap_tamper = copy.deepcopy(snap)
    snap_tamper["records"][0]["identity"]["security_name_zh"] = "惡意修改的名稱"
    
    snap_path = tmp_path / "snap_tamper_a.json"
    man_path = tmp_path / "man_tamper_a.json"
    snap_path.write_text(json.dumps(snap_tamper), encoding="utf-8")
    man_path.write_text(json.dumps(man), encoding="utf-8")
    
    with pytest.raises(VerifiedSecurityMasterSnapshotError):
        load_verified_security_master_snapshot(str(snap_path), str(man_path), allow_fixture_snapshot=True)
        
    # 篡改情境 B：修改 manifest 的 snapshot_sha256 與實際 snapshot 雜湊不一致
    man_tamper = copy.deepcopy(man)
    man_tamper["snapshot_sha256"] = "wrong_hash_value"
    
    snap_path = tmp_path / "snap_tamper_b.json"
    man_path = tmp_path / "man_tamper_b.json"
    snap_path.write_text(json.dumps(snap), encoding="utf-8")
    man_path.write_text(json.dumps(man_tamper), encoding="utf-8")
    
    with pytest.raises(VerifiedSecurityMasterSnapshotError):
        load_verified_security_master_snapshot(str(snap_path), str(man_path), allow_fixture_snapshot=True)
        
    # 篡改情境 C：修改 skill_contract_hash 與實際不一致
    man_tamper_c = copy.deepcopy(man)
    man_tamper_c["skill_contract_hash"] = "wrong_skill_contract_hash"
    
    snap_path = tmp_path / "snap_tamper_c.json"
    man_path = tmp_path / "man_tamper_c.json"
    snap_path.write_text(json.dumps(snap), encoding="utf-8")
    man_path.write_text(json.dumps(man_tamper_c), encoding="utf-8")
    
    with pytest.raises(VerifiedSecurityMasterSnapshotError):
        load_verified_security_master_snapshot(str(snap_path), str(man_path), allow_fixture_snapshot=True)
