import json
from pathlib import Path
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package, ptr_get, sha256_json

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def test_manifest_hash_and_artifact_integrity():
    manifest = load("fixture_manifest.json")
    
    # 1. 驗證不可歧義的 manifest hash contract
    man_copy = dict(manifest)
    man_copy["artifacts"][0]["sha256"] = ""
    man_copy.pop("manifest_hash", None)
    expected_manifest_hash = sha256_json(man_copy)
    assert manifest["manifest_hash"] == expected_manifest_hash, "Manifest self-hash contract violated or mismatched"
    
    # 2. 逐一讀取 13 個 artifacts，校對其在 manifest 中的 sha256 雜湊與 target_ids
    tids = manifest["target_ids"]
    assert len(tids) == 10
    
    # 用於驗證是否每個在 artifacts 列表中的檔案都有確實被讀取與核對
    verified_count = 0
    for art in manifest["artifacts"]:
        rel_path = art["relative_path"]
        
        # 讀取檔案重算 sha256
        file_path = FIX_DIR / rel_path
        assert file_path.exists(), f"Artifact file not found on disk: {rel_path}"
        
        file_bytes = file_path.read_bytes()
        file_json = json.loads(file_bytes.decode("utf-8"))
        actual_sha256 = sha256_json(file_json)
        
        # 如果是 manifest 自身，其在 entry 的 sha256 為空字串
        if art["artifact_type"] == "fixture_manifest":
            assert art["sha256"] == ""
        else:
            assert art["sha256"] == actual_sha256, f"Hash drift in artifact: {rel_path}"
            
        # 驗證 target_ids 補齊情況
        if art["artifact_type"] not in {"fixture_manifest", "source_capability_snapshot"}:
            assert art["target_ids"] == tids, f"Empty or incorrect target_ids in artifact entry: {rel_path}"
            
        verified_count += 1
        
    assert verified_count == 13, "Expected exactly 13 artifacts in the manifest"

def test_package_hash_and_citation_provenance():
    pkg = load("context_projection.json")
    req = load("bounded_request.json")
    plan = load("execution_plan.json")
    bundle = load("evidence_bundle.json")
    
    # 模擬 execution_result 結構
    result = {
        "schema_version": "m8r_03d_watchlist_execution_result.v1",
        "run_id": "temp_run",
        "plan_id": plan["plan_id"],
        "request_id": req["request_id"],
        "request_hash": plan["request_hash"],
        "status": "success",
        "mode": "fixture"
    }
    
    # 1. 驗證整體 package 驗證通過 (內部會重新計算並校對 package_hash)
    val = validate_watchlist_ai_context_package(
        pkg,
        upstream_artifacts={
            "validated_request": req,
            "execution_plan": plan,
            "execution_result": result,
            "watchlist_bundle": bundle
        }
    )
    assert val["valid"], f"Package validation failed: {val['issues']}"
    
    # 2. 手動驗證每個 citation 雜湊
    cids_in_index = set()
    for c in pkg["citation_index"]:
        cid = c["citation_id"]
        cids_in_index.add(cid)
        
        # 提取 fact 值並雜湊比對
        val_in_pkg = ptr_get(pkg, c["fact_path"])
        expected_hash = sha256_json(val_in_pkg)
        assert c["value_hash"] == expected_hash, f"Hash mismatch for citation {cid}"
        
        # 驗證 provenance 鏈
        assert c["source_artifact_type"] in {"execution_plan", "watchlist_bundle"}
        assert c["source_artifact_id"] in {plan["plan_id"], bundle["bundle_id"]}
        
    # 3. 驗證沒有 orphan citations (所有 target 的 citations 都有在 index 內)
    for t in pkg["targets"]:
        for cid in t["citations"]:
            assert cid in cids_in_index, f"Orphan citation {cid} found in target {t['target_id']}"
