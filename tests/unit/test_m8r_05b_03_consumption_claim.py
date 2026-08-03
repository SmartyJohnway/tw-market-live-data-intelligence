from __future__ import annotations

import json
from copy import deepcopy
from threading import Thread

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.consumption_claim import (
    atomic_claim_authorization,
    build_claim_record,
    claim_relative_path,
    validate_claim_destination,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    ROOT,
    artifacts,
    build_valid_preflight,
)


def test_first_claim_succeeds_and_second_claim_fails(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)

    record, rel_path = atomic_claim_authorization(
        preflight,
        state,
        output_root=str(tmp_path),
        claim_created_at=CLAIM_TIMESTAMP,
    )
    assert record["state"] == "claimed"
    assert rel_path == claim_relative_path(authorization["authorization_id"])
    assert (tmp_path / rel_path).exists()

    with pytest.raises(OrchestrationError, match="authorization_already_claimed"):
        atomic_claim_authorization(
            preflight,
            state,
            output_root=str(tmp_path),
            claim_created_at=CLAIM_TIMESTAMP,
        )


def test_two_concurrent_claims_produce_exactly_one_winner(tmp_path):
    _plan, _authorization, _binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)

    results = []
    errors = []

    def _worker():
        try:
            rec, path = atomic_claim_authorization(
                preflight,
                deepcopy(state),
                output_root=str(tmp_path),
                claim_created_at=CLAIM_TIMESTAMP,
            )
            results.append((rec, path))
        except OrchestrationError as exc:
            errors.append(exc.code)

    t1 = Thread(target=_worker)
    t2 = Thread(target=_worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(results) == 1
    assert len(errors) == 1
    assert errors[0] == "authorization_already_claimed"


def test_claimed_supplied_state_rejected(tmp_path):
    _plan, _authorization, _binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    claimed_state = deepcopy(state)
    claimed_state["state"] = "claimed"

    with pytest.raises(OrchestrationError, match="authorization_already_claimed"):
        build_claim_record(preflight, claimed_state, claim_created_at=CLAIM_TIMESTAMP)


def test_authorization_and_binding_mismatch_rejected(tmp_path):
    _plan, _authorization, _binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)

    bad_auth_state = deepcopy(state)
    bad_auth_state["authorization_id"] = "umea-v1-00000000000000000000"
    with pytest.raises(OrchestrationError, match="consumption_authorization_mismatch"):
        build_claim_record(preflight, bad_auth_state, claim_created_at=CLAIM_TIMESTAMP)

    bad_binding_state = deepcopy(state)
    bad_binding_state["consumption_binding_id"] = "umeacb-v1-00000000000000000000"
    with pytest.raises(OrchestrationError, match="consumption_binding_state_mismatch"):
        build_claim_record(preflight, bad_binding_state, claim_created_at=CLAIM_TIMESTAMP)


def test_registry_contract_version_mismatch_rejected(tmp_path):
    _plan, _authorization, _binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    bad_registry_state = deepcopy(state)
    bad_registry_state["registry_contract_version"] = "m8r_05b_02.v1"
    with pytest.raises(OrchestrationError, match="registry_contract_mismatch"):
        build_claim_record(preflight, bad_registry_state, claim_created_at=CLAIM_TIMESTAMP)


def test_invalid_claim_timestamp_rejected(tmp_path):
    _plan, _authorization, _binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)

    with pytest.raises(OrchestrationError, match="claim_timestamp_invalid"):
        build_claim_record(preflight, state, claim_created_at="not-a-timestamp")


def test_claim_record_schema_validation(tmp_path):
    schema = json.loads((ROOT / "schemas/unified_market_evidence_consumption_record.v1.schema.json").read_text(encoding="utf-8"))
    _plan, _authorization, _binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    record = build_claim_record(preflight, state, claim_created_at=CLAIM_TIMESTAMP)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert list(validator.iter_errors(record)) == []


def test_claim_path_containment(tmp_path):
    assert validate_claim_destination(str(tmp_path), "umea-v1-12345678901234567890") == "claims/umea-v1-12345678901234567890.consumption-record.json"
