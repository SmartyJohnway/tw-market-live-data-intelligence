import json
import shutil
import pytest
from pathlib import Path
from scripts.m8r_03e_r5a_cross_layer_fixture import generate_fixtures_to_disk

def test_fixture_byte_identical_determinism(tmp_path):
    # 建立一個固定的臨時絕對路徑，確保兩次生成的絕對路徑完全相同
    det_dir = tmp_path / "deterministic_run"
    det_dir.mkdir()
    
    # 第一次生成
    generate_fixtures_to_disk(det_dir, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    
    # 讀取第一次生成的全部檔案的原始 bytes 與 manifest 資訊
    first_run_bytes = {}
    first_run_files = sorted(list(det_dir.rglob("*")))
    for f in first_run_files:
        if f.is_file():
            first_run_bytes[f.name] = f.read_bytes()
            
    # 清空該目錄
    shutil.rmtree(det_dir)
    det_dir.mkdir()
    
    # 第二次生成
    generate_fixtures_to_disk(det_dir, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    
    # 對比第二次產生的原始 bytes，必須 100% 完全相同，不清洗任何欄位
    second_run_files = sorted(list(det_dir.rglob("*")))
    assert len(first_run_bytes) == len([f for f in second_run_files if f.is_file()])
    
    for f in second_run_files:
        if f.is_file():
            assert f.name in first_run_bytes, f"Missing file: {f.name}"
            # 驗證原始 bytes 100% 相同
            assert f.read_bytes() == first_run_bytes[f.name], f"Byte drift detected in file: {f.name}"

def test_fixture_different_seed_controlled_differences(tmp_path):
    path_a = tmp_path / "seed_a"
    path_b = tmp_path / "seed_b"
    path_a.mkdir()
    path_b.mkdir()
    
    # 相同 clock，不同 seed
    generate_fixtures_to_disk(path_a, seed_val="seed-12345", clock_val="2026-07-16T03:00:00Z")
    generate_fixtures_to_disk(path_b, seed_val="seed-67890", clock_val="2026-07-16T03:00:00Z")
    
    # 讀取 manifest
    man_a = json.loads((path_a / "fixture_manifest.json").read_text(encoding="utf-8"))
    man_b = json.loads((path_b / "fixture_manifest.json").read_text(encoding="utf-8"))
    
    # 驗證 seed 與 fixture_id 不同
    assert man_a["seed"] == "seed-12345"
    assert man_b["seed"] == "seed-67890"
    assert man_a["fixture_id"] != man_b["fixture_id"]
    assert man_a["manifest_hash"] != man_b["manifest_hash"]
    
    # 讀取 security master snapshot，驗證 seed-derived name suffix 不同
    sm_a = json.loads((path_a / "security_identity_snapshot.json").read_text(encoding="utf-8"))
    sm_b = json.loads((path_b / "security_identity_snapshot.json").read_text(encoding="utf-8"))
    
    # 驗證台積電的中文名稱帶有不同的 seed 尾綴
    name_a = sm_a["records"][0]["identity"]["security_name_zh"]
    name_b = sm_b["records"][0]["identity"]["security_name_zh"]
    assert name_a == "台積電-seed-12345"
    assert name_b == "台積電-seed-67890"
    
    # 讀取 observations，驗證價格因為隨機 seed 微調而產生控制內的不同
    obs_a = json.loads((path_a / "source_observations.json").read_text(encoding="utf-8"))
    obs_b = json.loads((path_b / "source_observations.json").read_text(encoding="utf-8"))
    price_a = obs_a["targets"]["TWSE:2330"]["TWSE_MIS"]["price"]
    price_b = obs_b["targets"]["TWSE:2330"]["TWSE_MIS"]["price"]
    assert price_a != price_b

def test_fixture_different_clock_controlled_differences(tmp_path):
    path_a = tmp_path / "clock_a"
    path_b = tmp_path / "clock_b"
    path_a.mkdir()
    path_b.mkdir()
    
    # 相同 seed，不同 clock
    generate_fixtures_to_disk(path_a, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    generate_fixtures_to_disk(path_b, seed_val="test-seed", clock_val="2026-07-16T04:00:00Z")
    
    # 讀取 observations，驗證除了 timestamp 外，靜態資料的原始 bytes 完全一致
    obs_a = json.loads((path_a / "source_observations.json").read_text(encoding="utf-8"))
    obs_b = json.loads((path_b / "source_observations.json").read_text(encoding="utf-8"))
    
    # 清除 time-derived 欄位
    for o in (obs_a, obs_b):
        for target in o["targets"].values():
            for family in target.values():
                if "retrieved_at" in family: family["retrieved_at"] = "CLEANED"
                if "retrieved_at_utc" in family: family["retrieved_at_utc"] = "CLEANED"
                
    assert obs_a == obs_b

def test_fixture_different_output_roots_determinism(tmp_path):
    root_x = tmp_path / "root_x"
    root_y = tmp_path / "root_y"
    root_x.mkdir()
    root_y.mkdir()
    
    # 相同 seed 相同 clock，不同輸出目錄
    generate_fixtures_to_disk(root_x, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    generate_fixtures_to_disk(root_y, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    
    # 讀取 manifest 中列出的 canonical artifacts，核對原始 bytes
    manifest = json.loads((root_x / "fixture_manifest.json").read_text(encoding="utf-8"))
    
    for art in manifest["artifacts"]:
        rel = art["relative_path"]
        file_x = root_x / rel
        file_y = root_y / rel
        
        assert file_x.exists()
        assert file_y.exists()
        
        # 斷言不同輸出目錄下對應檔案的原始 bytes 100% 完全相同
        assert file_x.read_bytes() == file_y.read_bytes(), f"Byte drift under different output root for: {rel}"
