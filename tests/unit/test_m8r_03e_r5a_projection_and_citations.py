import json
from pathlib import Path
from scripts.m8r_03c_conversation_contract_validator import FORBIDDEN_KEYS

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def assert_no_secrets(val, path="$"):
    if isinstance(val, dict):
        for k, v in val.items():
            assert str(k).lower() not in FORBIDDEN_KEYS, f"Forbidden key {k} at {path}"
            assert_no_secrets(v, f"{path}.{k}")
    elif isinstance(val, list):
        for i, v in enumerate(val):
            assert_no_secrets(v, f"{path}[{i}]")

def test_projection_has_no_sensitive_data():
    pkg = load("context_projection.json")
    assert_no_secrets(pkg)

def test_target_states_match_expectations():
    pkg = load("context_projection.json")
    
    # 將 target 映射為 id -> object
    t_map = {t["target_id"]: t for t in pkg["targets"]}
    
    # 1. TWSE:2330: 正常雙軌 -> supported
    t_2330 = t_map["TWSE:2330"]
    assert t_2330["coverage"]["evidence_states"]["identity"] == "supported"
    assert t_2330["coverage"]["evidence_states"]["current_observation"] == "supported"
    assert t_2330["coverage"]["evidence_states"]["eod_reference"] == "supported"
    
    # 2. TWSE:2317: live-ish 失敗但 EOD fallback 成功 -> partial coverage
    t_2317 = t_map["TWSE:2317"]
    assert t_2317["coverage"]["evidence_states"]["current_observation"] == "unavailable"
    assert t_2317["coverage"]["evidence_states"]["eod_reference"] == "supported"
    assert t_2317["coverage"]["coverage_state"] == "partial"
    
    # 3. TPEX:6488: EOD 單軌
    t_6488 = t_map["TPEX:6488"]
    assert t_6488["coverage"]["evidence_states"]["current_observation"] == "unavailable"
    assert t_6488["coverage"]["evidence_states"]["eod_reference"] == "supported"
    assert t_6488["coverage"]["coverage_state"] == "partial"
    
    # 7. TWSE:2308: stale but usable (由於有數據，仍然是 supported，但其 citation_index 的 currentness 會有 stale)
    t_2308 = t_map["TWSE:2308"]
    assert t_2308["coverage"]["evidence_states"]["current_observation"] == "supported"
    assert t_2308["coverage"]["evidence_states"]["eod_reference"] == "supported"
    assert t_2308["coverage"]["coverage_state"] == "usable"
    
    # 8. TWSE:2382: missing optional (EOD unavailable)
    t_2382 = t_map["TWSE:2382"]
    assert t_2382["coverage"]["evidence_states"]["current_observation"] == "supported"
    assert t_2382["coverage"]["evidence_states"]["eod_reference"] == "unavailable"
    # 因為是 optional 缺失，所以在 budget 重新計算後，為 partial 狀態
    assert t_2382["coverage"]["coverage_state"] == "partial"
    
    # 10. TWSE:9999: unresolved/quarantined -> unavailable
    t_9999 = t_map["TWSE:9999"]
    assert t_9999["coverage"]["coverage_state"] == "unavailable"
    assert t_9999["coverage"]["evidence_states"]["identity"] == "unavailable"
    
    # 驗證 missing evidence 中有 TWSE:9999 且 reason_code 為 identity_unresolved
    miss_reg = load("missing_evidence_register.json")
    unresolved_items = [m for m in miss_reg if m["target_id"] == "TWSE:9999" and m["reason_code"] == "identity_unresolved"]
    assert len(unresolved_items) >= 1
