import json
from pathlib import Path
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package, ptr_get, sha256_json

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

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
