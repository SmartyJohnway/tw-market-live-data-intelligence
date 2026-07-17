import json
from pathlib import Path
from scripts.m8r_03e_context_validator import validate_m8r_03e_upstream_artifacts, validate_watchlist_ai_context_package

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def test_cross_layer_id_and_order_consistency():
    req = load("bounded_request.json")
    plan = load("execution_plan.json")
    bundle = load("evidence_bundle.json")
    pkg = load("context_projection.json")
    
    # 1. 驗證 request_id
    rid = req["request_id"]
    assert rid == "m8r03c-snapshot"
    assert plan["request_id"] == rid
    assert bundle["request_id"] == rid
    assert pkg["request"]["request_id"] == rid
    
    # 2. 驗證 plan_id
    pid = plan["plan_id"]
    assert pkg["source_lineage"]["plan_id"] == pid
    
    # 3. 驗證 target_id 順序與一致性
    req_targets = req["persistent_watchlist_reference"]["enabled_target_ids"]
    assert len(req_targets) == 10
    
    plan_targets = plan["target_order"]
    assert plan_targets == req_targets
    
    bundle_targets = bundle["coverage"]["requested_target_ids"]
    assert bundle_targets == req_targets
    
    pkg_targets = [t["target_id"] for t in pkg["targets"]]
    assert pkg_targets == req_targets
    
    # 4. 驗證 resolved vs unresolved
    for t in plan["targets"]:
        tid = t["target_id"]
        pkg_t = next(x for x in pkg["targets"] if x["target_id"] == tid)
        
        if t["identity_status"] == "resolved":
            assert pkg_t["coverage"]["evidence_states"]["identity"] == "supported"
            assert pkg_t["identity"]["security_code"] == t["security_code"]
            assert pkg_t["identity"].get("record_hash") is not None
        else:
            assert pkg_t["coverage"]["evidence_states"]["identity"] == "unavailable"
            # 即使是 unresolved，security_code 依然會從 target_id 解析出來，所以我們透過 record_hash 為 None 來驗證 unresolved
            assert pkg_t["identity"].get("record_hash") is None

def test_upstream_validation_passes():
    req = load("bounded_request.json")
    plan = load("execution_plan.json")
    bundle = load("evidence_bundle.json")
    
    # 用真實執行結果的 execution_result 結構來驗證
    result = {
        "schema_version": "m8r_03d_watchlist_execution_result.v1",
        "run_id": "temp_run",
        "plan_id": plan["plan_id"],
        "request_id": req["request_id"],
        "request_hash": plan["request_hash"],
        "status": "success",
        "mode": "fixture",
        "source_execution_summary": {
            "group_results": [
                {
                    "source_family": g["source_family"],
                    "target_ids": g["target_ids"],
                    "status": "success",
                    "observation_count": len(g["target_ids"])
                }
                for g in plan["source_call_groups"]
            ]
        }
    }
    
    val = validate_m8r_03e_upstream_artifacts(
        validated_request=req,
        execution_plan=plan,
        execution_result=result,
        watchlist_bundle=bundle
    )
    
    assert val["valid"], f"Upstream validation failed: {val['issues']}"
