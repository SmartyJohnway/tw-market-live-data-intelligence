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
        "consumption_claim_id": claim_id,
        "consumption_claim_hash": "placeholder",
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "operator_confirmation_reference": {
            "operator_id": "system",
            "workstation_id": "test",
            "intended_use_statement": "test",
            "operator_attestation": True
        },
        "output_root": str(FIXTURE_DIR / "artifact_root"),
        "destination_policy_status": "enforced",
        "created_at": "2026-08-01T02:05:00Z"
    }

    receipt = load_json("receipt.json")
    bundle = load_json("bundle.json")

    # 1. Update Plan input bindings
    request_hash = sha256_json(request)
    normalized_request_hash = sha256_json(f3_validation["normalized_request"])
    f3_validation["normalized_request_hash"] = normalized_request_hash
    f3_hash = sha256_json(f3_validation)
    
    plan["input_bindings"]["original_request_hash"] = request_hash
    plan["input_bindings"]["f3_validation_output_hash"] = f3_hash
    plan["input_bindings"]["normalized_request_hash"] = normalized_request_hash
    
    plan_body = deepcopy(plan)
    plan_body.pop("plan_hash", None)
    plan_hash = sha256_json(plan_body)
    plan["plan_hash"] = plan_hash
    
    # 2. Update Authorization
    authorization["plan_hash"] = plan_hash
    authorization["input_bindings"] = plan["input_bindings"]
    authorization["authorization_identity_scope"]["plan_hash"] = plan_hash
    authorization["authorization_identity_scope"]["input_bindings"] = plan["input_bindings"]
    
    auth_body = deepcopy(authorization)
    auth_body.pop("authorization_hash", None)
    auth_body.pop("plan_binding_hash", None)
    auth_body.pop("scope_hash", None)
    
    authorization["authorization_hash"] = sha256_json(auth_body)
    
    # 3. Update Binding
    consumption_binding["authorization_hash"] = authorization["authorization_hash"]
    consumption_binding["plan_hash"] = plan_hash
    binding_body = deepcopy(consumption_binding)
    binding_body.pop("consumption_binding_hash", None)
    consumption_binding["consumption_binding_hash"] = sha256_json(binding_body)
    
    # 4. Update Claim
    claim["consumption_binding_hash"] = consumption_binding["consumption_binding_hash"]
    claim["authorization_hash"] = authorization["authorization_hash"]
    claim["plan_hash"] = plan_hash
    
    claim_body = deepcopy(claim)
    claim_body.pop("consumption_claim_hash", None)
    claim["consumption_claim_hash"] = sha256_json(claim_body)
    
    # 5. Update Receipt
    receipt["claim_hash"] = claim["consumption_claim_hash"]
    receipt["authorization_hash"] = authorization["authorization_hash"]
    receipt["plan_hash"] = plan_hash
    receipt_body = deepcopy(receipt)
    receipt_body.pop("execution_receipt_hash", None)
    receipt["execution_receipt_hash"] = sha256_json(receipt_body)
    
    # 6. Update Bundle
    bundle["execution_receipt_hash"] = receipt["execution_receipt_hash"]
    bundle["authorization_hash"] = authorization["authorization_hash"]
    bundle["claim_hash"] = claim["consumption_claim_hash"]
    bundle_body = deepcopy(bundle)
    bundle_body.pop("bundle_hash", None)
    bundle["bundle_hash"] = sha256_json(bundle_body)
    
    # Save all
    save_json(f3_validation, "f3_validation.json")
    save_json(plan, "plan_single_target.json")
    save_json(authorization, "authorization.json")
    save_json(consumption_binding, "consumption_binding.json")
    save_json(claim, "claim.json")
    save_json(receipt, "receipt.json")
    save_json(bundle, "bundle.json")

    print("Fixtures lineage patched successfully.")

if __name__ == "__main__":
    main()
