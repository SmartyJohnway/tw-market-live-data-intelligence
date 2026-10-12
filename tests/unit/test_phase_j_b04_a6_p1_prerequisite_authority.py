from __future__ import annotations

import json
from pathlib import Path

from scripts.phase_j_b04_a6_p1_prerequisite_authority import (
    BOOTSTRAP_AUTHORIZATION_TEMPLATE,
    EXPECTED_LOGICAL_PROBES,
    classify_bootstrap_dispatch,
    bootstrap_authorization_template,
    h2_activation_current_state,
    h3_automation_authority,
    post_bootstrap_identity_acceptance,
    source_inventory,
)


def test_bootstrap_inventory_is_the_five_materializer_probes_and_manifest_hosts():
    inventory = source_inventory()
    assert len(inventory) == 5
    assert [item["source_id"] for item in inventory] == [
        "twse_isin_mode2_zh",
        "twse_isin_mode4_zh",
        "twse_delisted",
        "tpex_delisted",
        "twse_etn_expired",
    ]
    assert all(item["allowed_host_present"] for item in inventory)
    assert {item["source_id"]: item["http_method"] for item in inventory} == {
        "twse_isin_mode2_zh": "GET",
        "twse_isin_mode4_zh": "GET",
        "twse_delisted": "GET",
        "tpex_delisted": "POST",
        "twse_etn_expired": "GET",
    }
    assert next(item for item in inventory if item["source_id"] == "tpex_delisted")["initial_url"] == "https://www.tpex.org.tw/www/zh-tw/company/deListed"
    etn = next(item for item in inventory if item["source_id"] == "twse_etn_expired")
    assert etn["initial_url"] == "https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json"
    assert etn["parser"] == "parse_twse_etn_expired_json"
    assert all(item["timeout_seconds"] == 20 for item in inventory)
    assert all(item["response_size_bound_bytes"] == 20 * 1024 * 1024 for item in inventory)
    assert all(item["source_contract_identifier"] is None for item in inventory)
    assert len(EXPECTED_LOGICAL_PROBES) == 5


def test_redirect_dispatch_uses_inherited_runtime_values_and_project_bound():
    from scripts.phase_j_b04_a6_p1_prerequisite_authority import inspect_redirect_runtime_bounds

    bounds = inspect_redirect_runtime_bounds()
    assert bounds["is_subclass"] is True
    assert isinstance(bounds["max_repeats"], int) and bounds["max_repeats"] > 0
    assert isinstance(bounds["max_redirections"], int) and bounds["max_redirections"] > 0
    assert classify_bootstrap_dispatch() == "PROJECT_OWNED_BOUNDED"
    metadata = bootstrap_authorization_template()
    assert metadata["template_type"] == "FUTURE_OWNER_AUTHORIZATION_METADATA_ONLY"
    assert metadata["authorization_status"] == "NOT_AUTHORIZED"
    assert BOOTSTRAP_AUTHORIZATION_TEMPLATE["bootstrap_http_dispatch_hard_ceiling"] == 10


def test_post_bootstrap_identity_contract_requires_production_exact_identity():
    identity = {
        "manager_status": "ACTIVE",
        "release_state": "QUALIFIED",
        "manifest_hash_valid": True,
        "production_loader": "PASS",
        "resolution_status": "resolved",
        "reason": "exact_listing_id",
        "canonical_target_id": "TWSE:2330",
        "market": "TWSE",
        "security_code": "2330",
        "instrument_family": "company_share",
        "instrument_type": "common_share",
        "execution_eligibility": "allowed",
        "release_id": "security-master-20261009T000000Z",
        "manifest_sha256": "a" * 64,
        "release_index_sha256": "b" * 64,
        "active_selector": "active.json",
        "isin": "TW0002330008",
    }
    assert post_bootstrap_identity_acceptance(identity)
    assert not post_bootstrap_identity_acceptance({**identity, "reason": "company_name_match"})
    assert not post_bootstrap_identity_acceptance({**identity, "execution_eligibility": "blocked"})
    assert not post_bootstrap_identity_acceptance({**identity, "manager_status": "NOT_INITIALIZED"})


def test_h3_authority_parser_separates_owner_use_from_provider_permission():
    path = Path("docs/governance/phase_h/PHASE_H_H3_TWSE_CONTROLLED_USE_OWNER_DECISION_2026-09-24.json")
    decision = h3_automation_authority(json.loads(path.read_text(encoding="utf-8")))
    assert decision["disposition"] == "J_B04_A6_H3_AUTOMATION_AUTHORITY_ACCEPTED"
    assert decision["provider_automation_permission"] == "NOT_ESTABLISHED_TERMS_CONFLICTED"
    assert decision["provider_approval_claimed"] is False
    assert decision["owner_product_authorization"] == "APPROVED_CONTROLLED_LOCAL_FIRST_USE"


def test_h2_remains_plan_only_inactive_and_unselected():
    state = h2_activation_current_state()
    assert state["catalog"]["runtime_executable"] is False
    assert state["catalog"]["phase_h_activation_state"] == "inactive"
    assert state["routing"]["runtime_executable"] is False
    assert state["routing"]["routing_status"] == "plan_only"
    assert state["routing"]["selected_executor_id"] is None


def test_inventory_and_authority_helpers_are_network_free(monkeypatch):
    import socket

    def denied(*_args, **_kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", denied)
    assert len(source_inventory()) == 5
    assert classify_bootstrap_dispatch() == "PROJECT_OWNED_BOUNDED"
    assert h2_activation_current_state()["catalog"]["runtime_executable"] is False
