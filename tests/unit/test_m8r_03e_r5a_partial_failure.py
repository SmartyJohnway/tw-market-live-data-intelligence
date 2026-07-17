import copy
import json
from pathlib import Path
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def test_variant_c_tampering_fail_closed():
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
    
    # 正常情況應通過
    val = validate_watchlist_ai_context_package(pkg, upstream_artifacts={"validated_request": req, "execution_plan": plan, "execution_result": result, "watchlist_bundle": bundle})
    assert val["valid"]
    
    # 進行 Variant C：惡意篡改資料
    tampered_pkg = copy.deepcopy(pkg)
    # 修改台積電的最新價，但故意不改其對應的 value_hash
    assert tampered_pkg["targets"][0]["current_observation"]["latest_price"] == 1000.0
    tampered_pkg["targets"][0]["current_observation"]["latest_price"] = 9999.0
    
    # 校驗應失敗且攔截
    val_tampered = validate_watchlist_ai_context_package(
        tampered_pkg, 
        upstream_artifacts={
            "validated_request": req, 
            "execution_plan": plan, 
            "execution_result": result, 
            "watchlist_bundle": bundle
        }
    )
    assert not val_tampered["valid"]
    # 應能指出 citation_value_hash_mismatch 或是 value_hash 不對等
    assert any("hash" in i["code"] or "mismatch" in i["code"] or "fail" in i["code"] for i in val_tampered["issues"])

def test_variant_b_stale_and_missing_mix():
    pkg = load("context_projection.json")
    t_map = {t["target_id"]: t for t in pkg["targets"]}
    
    # 7. TWSE:2308: 包含 stale status
    co_2308 = t_map["TWSE:2308"]["current_observation"]
    assert co_2308["currentness_status"] == "stale"
    
    # 8. TWSE:2382: 缺失 optional EOD (unavailable)
    assert t_map["TWSE:2382"]["eod_reference"] == {}
    
    # 10. TWSE:9999: unresolved 隔離且無 data
    assert t_map["TWSE:9999"]["current_observation"] == {}
    assert t_map["TWSE:9999"]["eod_reference"] == {}
