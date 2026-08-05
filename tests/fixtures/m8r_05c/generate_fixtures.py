"""Fixes cryptographic lineage in M8R-05C fixtures."""

import json
from pathlib import Path
from copy import deepcopy

from scripts.m8r_05b_03.canonical import sha256_json

FIXTURE_DIR = Path(__file__).parent

def load_json(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, name):
    with open(FIXTURE_DIR / name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def main():
    request = load_json("request_single_target.json")
    f3_validation = load_json("f3_validation.json")
    plan = load_json("plan_single_target.json")
    authorization = load_json("authorization.json")
    consumption_binding = load_json("consumption_binding.json")
    
    # We don't have claim.json yet. So let's create it.
    claim_id = "umecl-v1-cdd785afa40a3def8cf5"
    claim = {
        "schema_version": "unified_market_evidence_consumption_record.v1",
        "claim_id": claim_id,
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "scope_hash": authorization["scope_hash"],
        "operator_confirmation_reference": "system",
        "preflight_id": "umeopf-v1-aaaabbbbccccdddd0000",
        "preflight_identity_hash": "25f54ccf69ba54e601556094fc6127bcfb92d6e38202513f56e0ebc19bd183f3",
        "preflight_artifact_hash": "4225026dfab055f187a8ceaf5a4be46dbf87c2fb8bcfd7d5669b76eabdf9d436",
        "execution_mode": "execute-approved",
        "execution_confirmed": True,
        "network_execution_confirmed": True,
        "confirmation_bound_at": "2026-08-01T02:05:00Z",
        "state": "consumed_success",
        "claim_created_at": "2026-08-01T02:05:00Z",
        "claimed_by_component": "m8r_05c_test",
        "attempt_count": 1,
        "execution_receipt_id": "umer-v1-00000000000000000000",
        "execution_receipt_hash": "1111111111111111111111111111111111111111111111111111111111111111",
        "finalized_at": "2026-08-01T02:05:00Z",
        "last_error_code": None
    }

    receipt = load_json("receipt.json")
    bundle = load_json("bundle.json")

    # 1. Update Plan input bindings
    request_hash = sha256_json(request)
    normalized_request_hash = sha256_json(f3_validation["normalized_request"])
    f3_hash = sha256_json(f3_validation)
    
    plan["input_bindings"]["original_request_hash"] = request_hash
    plan["input_bindings"]["f3_validation_output_hash"] = f3_hash
    plan["input_bindings"]["normalized_request_hash"] = normalized_request_hash
    
    from scripts.m8r_05b_01.planner import plan_identity_scope
    from scripts.m8r_05b_01.canonical import plan_hash_and_id
    
    scope = plan_identity_scope(plan)
    plan_hash, plan_id = plan_hash_and_id(scope)
    plan["plan_hash"] = plan_hash
    plan["plan_id"] = plan_id
    
    from scripts.m8r_05b_02.authorization import _derived
    from scripts.m8r_05b_02.canonical import authorization_identity

    # 2. Update Authorization
    authorization["plan_id"] = plan_id
    authorization["plan_hash"] = plan_hash
    authorization["input_bindings"] = plan["input_bindings"]
    authorization["authorization_identity_scope"]["plan_hash"] = plan_hash
    authorization["authorization_identity_scope"]["input_bindings"] = plan["input_bindings"]
    
    derived = _derived(plan, authorization["approval_scope_mode"], authorization)
    authorization["scope_hash"] = sha256_json(derived)
    for k, v in derived.items():
        authorization[k] = v
    
    bind = {
        "schema_version": plan.get("schema_version"),
        "plan_id": plan.get("plan_id"),
        "plan_hash": plan.get("plan_hash"),
        "input_bindings": plan.get("input_bindings"),
        "scope": derived
    }
    authorization["plan_binding_hash"] = sha256_json(bind)
    
    auth_hash, auth_id = authorization_identity(authorization["authorization_identity_scope"])
    authorization["authorization_hash"] = auth_hash
    authorization["authorization_id"] = auth_id
    
    from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
    
    # 3. Update Binding
    consumption_binding = build_consumption_binding(authorization)
    
    # 4. Update Claim
    claim["consumption_binding_id"] = consumption_binding["consumption_binding_id"]
    claim["consumption_binding_hash"] = consumption_binding["consumption_binding_hash"]
    claim["authorization_id"] = authorization["authorization_id"]
    claim["authorization_hash"] = authorization["authorization_hash"]
    claim["plan_id"] = plan_id
    claim["plan_hash"] = plan_hash
    claim["scope_hash"] = authorization["scope_hash"]
    
    # claim_hash is computed dynamically and is NOT part of the schema
    claim_hash = sha256_json(claim)
    
    # 5. Update Receipt
    receipt["claim_hash"] = claim_hash
    receipt_body = deepcopy(receipt)
    receipt_body.pop("execution_receipt_hash", None)
    receipt["execution_receipt_hash"] = sha256_json(receipt_body)
    
    # 6. Update Bundle
    bundle["claim_hash"] = claim_hash
    bundle["execution_receipt_hash"] = receipt["execution_receipt_hash"]
    bundle["execution_receipt_id"] = receipt["execution_receipt_id"]
    bundle["authorization_hash"] = authorization["authorization_hash"]
    bundle["authorization_id"] = authorization["authorization_id"]
    bundle["claim_hash"] = claim_hash
    bundle_body = deepcopy(bundle)
    bundle_body.pop("bundle_hash", None)
    bundle["bundle_hash"] = sha256_json(bundle_body)
    
    # Save all
    save_json(plan, "plan_single_target.json")
    save_json(authorization, "authorization.json")
    save_json(consumption_binding, "consumption_binding.json")
    save_json(claim, "claim.json")
    save_json(receipt, "receipt.json")
    save_json(bundle, "bundle.json")

    print("Fixtures lineage patched successfully.")

if __name__ == "__main__":
    main()
