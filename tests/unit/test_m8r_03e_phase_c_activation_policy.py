import json
from pathlib import Path

def test_activation_policy_structure():
    path = Path("docs/data_capabilities/m8r_03e_phase_c_activation_policy.json")
    assert path.exists(), "Activation policy JSON must exist"
    
    policy = json.loads(path.read_text(encoding="utf-8"))
    assert policy.get("schema_version") == "m8r_phase_c_activation_policy.v1"
    assert policy.get("activation_profile_id") == "phase_c_conversation_driven_one_shot.v1"
    assert policy.get("activation_state") == "enabled_with_caveats"
    
    # 檢查 bounds
    bounds = policy.get("resource_bounds")
    assert bounds is not None
    assert bounds.get("default_max_targets") == 10
    assert bounds.get("hard_max_targets") == 50
    assert bounds.get("default_max_operations") == 30
    assert bounds.get("hard_max_operations") == 100
    
    # 檢查 features
    features = policy.get("non_activated_features")
    assert features is not None
    assert features.get("repository_internal_scheduler_enabled") is False
    assert features.get("repository_internal_polling_enabled") is False
    assert features.get("future_external_agent_repeated_execution_supported") is True
    assert features.get("future_repeated_execution_activated") is False
    assert features.get("autonomous_trading_enabled") is False
    assert features.get("order_execution_enabled") is False
