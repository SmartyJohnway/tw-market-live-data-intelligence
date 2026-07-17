import json
import pytest
import re
from pathlib import Path
from scripts.m8r_03e_r5a_cross_layer_fixture import generate_fixtures_to_disk

def clean_json_for_determinism(data: dict) -> dict:
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            # 清洗包含臨時路徑、run_id 還有任何隨機雜湊欄位
            if k in {
                "run_id", "artifact_paths", "created_at_utc", "generated_at_utc", 
                "manifest_hash", "package_hash", "sha256", "snapshot_sha256", 
                "schema_sha256", "skill_contract_hash"
            }:
                cleaned[k] = "CLEANED_FOR_TEST"
            elif isinstance(v, str) and ("pytest" in v or "Temp" in v or "run_" in v):
                cleaned[k] = "CLEANED_PATH"
            else:
                cleaned[k] = clean_json_for_determinism(v)
        return cleaned
    elif isinstance(data, list):
        return [clean_json_for_determinism(x) for x in data]
    else:
        return data

def test_fixture_determinism(tmp_path):
    path_a = tmp_path / "fixture_a"
    path_b = tmp_path / "fixture_b"
    path_a.mkdir()
    path_b.mkdir()
    
    # 相同 seed 相同 clock
    generate_fixtures_to_disk(path_a, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    generate_fixtures_to_disk(path_b, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    
    files_a = sorted(list(path_a.rglob("*.json")))
    files_b = sorted(list(path_b.rglob("*.json")))
    
    assert len(files_a) == len(files_b)
    for fa, fb in zip(files_a, files_b):
        assert fa.name == fb.name
        
        obj_a = json.loads(fa.read_text(encoding="utf-8"))
        obj_b = json.loads(fb.read_text(encoding="utf-8"))
        
        # 排除包含絕對路徑與雜湊變化的欄位後，比對內容
        assert clean_json_for_determinism(obj_a) == clean_json_for_determinism(obj_b)

def test_fixture_determinism_changes_with_clock(tmp_path):
    path_a = tmp_path / "fixture_a"
    path_b = tmp_path / "fixture_b"
    path_a.mkdir()
    path_b.mkdir()
    
    # 相同 seed 不同 clock
    generate_fixtures_to_disk(path_a, seed_val="test-seed", clock_val="2026-07-16T03:00:00Z")
    generate_fixtures_to_disk(path_b, seed_val="test-seed", clock_val="2026-07-16T04:00:00Z")
    
    manifest_a = json.loads((path_a / "fixture_manifest.json").read_text(encoding="utf-8"))
    manifest_b = json.loads((path_b / "fixture_manifest.json").read_text(encoding="utf-8"))
    
    assert manifest_a["reference_clock_utc"] == "2026-07-16T03:00:00Z"
    assert manifest_b["reference_clock_utc"] == "2026-07-16T04:00:00Z"
    assert manifest_a["manifest_hash"] != manifest_b["manifest_hash"]
