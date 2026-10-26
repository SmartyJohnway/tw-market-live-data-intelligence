"""R5.1 bounded journal publication and historical/current schema regressions."""
import copy
import json
from pathlib import Path

import pytest

from scripts.m8r_05b_03 import receipt
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_filesystem_safety import FilesystemSafetyError
from tests.unit.test_m8r_05b_03_receipt import (
    setup_dispatch_environment, FINALIZED_AT, TestTrueConcurrentFinalization,
)


def test_partial_journal_publication_enters_normal_owner_handling(tmp_path, monkeypatch):
    _, preflight, claim, claim_rel, aggregation = setup_dispatch_environment(tmp_path)
    complete = {}
    waits = []
    def competing_publication(root, relative, text):
        path = Path(root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        value = json.loads(text)
        value["finalization_owner_id"] = "umefo-v1-aaaaaaaaaaaaaaaaaaa0"
        complete.update(path=path, text=json.dumps(value))
        path.write_text("{", encoding="utf-8")
        raise FilesystemSafetyError("already_consumed_or_replayed")
    def stabilize(attempt):
        waits.append(attempt)
        complete["path"].write_text(complete["text"], encoding="utf-8")
    monkeypatch.setattr(receipt, "atomic_create_text_exclusive", competing_publication)
    monkeypatch.setattr(receipt, "_journal_stabilization_wait", stabilize)
    with pytest.raises(OrchestrationError, match="^finalization_in_progress$"):
        receipt.finalize_consumption_and_write_receipt(preflight, claim, claim_rel, aggregation,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
            finalization_owner_id="umefo-v1-bbbbbbbbbbbbbbbbbbb0")
    assert waits == [1]  # Invalid first read, complete valid second read.
    assert not list((tmp_path / "receipts").glob("*.json"))
    assert json.loads((tmp_path / claim_rel).read_text())["state"] == "claimed"


def test_persistent_malformed_journal_exhausts_bound_and_remains_corrupt(tmp_path, monkeypatch):
    _, preflight, claim, claim_rel, aggregation = setup_dispatch_environment(tmp_path)
    path = tmp_path / receipt.journal_relative_path(preflight["authorization_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{", encoding="utf-8")
    waits = []
    monkeypatch.setattr(receipt, "_journal_stabilization_wait", waits.append)
    with pytest.raises(OrchestrationError, match="^finalization_journal_corrupt$"):
        receipt.finalize_consumption_and_write_receipt(preflight, claim, claim_rel, aggregation,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
            finalization_owner_id="umefo-v1-bbbbbbbbbbbbbbbbbbb0")
    assert waits == list(range(1, receipt.JOURNAL_STABILIZATION_MAX_ATTEMPTS))
    assert path.read_text() == "{"
    assert json.loads((tmp_path / claim_rel).read_text())["state"] == "claimed"


@pytest.mark.parametrize("iteration", range(50))
def test_true_concurrency_stress_iteration(tmp_path, iteration):
    # Reuse the strict original test, including exact mutation-phase counters.
    # Each parametrized invocation has its own clean pytest tmp_path.
    TestTrueConcurrentFinalization().test_two_threads_single_mutation_owner(tmp_path)


@pytest.mark.parametrize("mutation", ["missing_required", "wrong_type", "both_surfaces_allow_null_complete", "embedded_drift"])
def test_activation_validator_rejects_retrieval_semantic_drift(monkeypatch, mutation):
    from scripts import validate_phase_i_i3_a4_activation as validator
    original = validator._json
    standalone = copy.deepcopy(original("schemas/cash_institutional_flow_context_evidence.v2.schema.json"))
    result = copy.deepcopy(original("schemas/unified_market_evidence_result.v3.schema.json"))
    embedded = result["definitions"]["cash_institutional_flow_context"]
    if mutation == "missing_required": standalone["required"].remove("retrieved_at")
    elif mutation == "wrong_type": standalone["properties"]["retrieved_at"]["type"] = "string"
    elif mutation == "both_surfaces_allow_null_complete":
        for surface in (standalone, embedded):
            surface["allOf"][-2]["then"]["properties"]["retrieved_at"]["type"] = ["string", "null"]
    else: embedded["allOf"][-2]["else"]["properties"]["retrieved_at"]["type"] = "string"
    def changed(relative):
        if relative == "schemas/cash_institutional_flow_context_evidence.v2.schema.json": return standalone
        if relative == "schemas/unified_market_evidence_result.v3.schema.json": return result
        return original(relative)
    monkeypatch.setattr(validator, "_json", changed)
    with pytest.raises(AssertionError): validator.validate()
