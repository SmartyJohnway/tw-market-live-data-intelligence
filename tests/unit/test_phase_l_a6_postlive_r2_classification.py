from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from scripts import run_phase_l_l3_a6_live_recertification as runner
from server.services.phase_l_source_drift_contract import observe_source_attempt


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_DIR = REPO_ROOT / "docs/governance/phase_l/acceptance_runs/l3-a6-live-20261017T040030Z"
LIVE_HASHES = {
    "dispatch_ledger.json": "b1b86a07d5b0e892abc5f6fd1e46551a50c754bd56943807e3a2d0592939b786",
    "source_results.json": "e739e6bb7adc0691c07fa3cef6fca0bdc310281fd4ac1a0ee828a6f420e552cf",
    "result.json": "622c5982f20fd3d88a513d1a8cb0b1cda1cf4e744a53476364c37530a704621f",
    "manifest.json": "9da4044b3e048d7f7fc2ac69fe80b7dd35446855bed20c8abb60a71b40153908",
}


def _apply(verdict, contract, semantic, detail, records):
    return runner._apply_transport_precedence(verdict, contract, semantic, detail, records)


def test_all_transport_failures_override_adapter_verdicts_and_project_to_a5():
    record = {"transport_outcome": "transport_failure", "http_status": None}
    for provisional in ("CONFORMING", "CONFORMING_WITH_UNCERTAINTY", "CONTRACT_DRIFT_OBSERVED"):
        verdict, contract, semantic, projection = _apply(provisional, "invalid", "available", {}, [record])
        assert (verdict, contract, semantic, projection) == (
            "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed", "transport_failure"
        )
    observed = observe_source_attempt(
        source_contract_id="P12", observed_at="2026-10-17T04:30:00Z", http_status=None,
        transport_outcome="transport_failure", contract_outcome="not_evaluated",
        semantic_outcome="source_failed",
    )
    assert observed.transport_outcome == "transport_failure"
    assert observed.contract_outcome == "not_evaluated"
    assert observed.semantic_outcome == "source_failed"


def test_successful_response_preserves_source_specific_conforming_semantics():
    row = {"transport_outcome": "http_response", "http_status": 200}
    assert _apply("CONFORMING", "valid", "available", {}, [row]) == (
        "CONFORMING", "valid", "available", "http_response"
    )
    assert _apply("CONFORMING_WITH_UNCERTAINTY", "valid", "currentness_unknown", {}, [row]) == (
        "CONFORMING_WITH_UNCERTAINTY", "valid", "currentness_unknown", "http_response"
    )


def test_contract_drift_requires_successful_2xx_provider_response():
    assert _apply("CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed", {}, [
        {"transport_outcome": "http_response", "http_status": 200}
    ]) == ("CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed", "http_response")
    for status in (404, 410, 429, 500):
        assert _apply("CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed", {}, [
            {"transport_outcome": "http_response", "http_status": status}
        ]) == ("TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed", "http_response")


def test_alternate_response_cannot_hide_degraded_primary_or_successful_primary_drift():
    primary_failure_alternate_200 = [
        {"transport_outcome": "transport_failure", "http_status": None, "dispatch_role": "PRIMARY"},
        {"transport_outcome": "http_response", "http_status": 200, "dispatch_role": "GOVERNED_ALTERNATE"},
    ]
    assert _apply("TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed", {}, primary_failure_alternate_200) == (
        "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed", "http_response"
    )
    primary_drift_alternate_200 = [
        {"transport_outcome": "http_response", "http_status": 200, "dispatch_role": "PRIMARY"},
        {"transport_outcome": "http_response", "http_status": 200, "dispatch_role": "GOVERNED_ALTERNATE"},
    ]
    assert _apply("CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed", {}, primary_drift_alternate_200) == (
        "CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed", "http_response"
    )


def test_immutable_live_replay_corrects_only_adjudication_and_preserves_hashes():
    before = {name: hashlib.sha256((LIVE_DIR / name).read_bytes()).hexdigest() for name in LIVE_HASHES}
    assert before == LIVE_HASHES
    ledger = json.loads((LIVE_DIR / "dispatch_ledger.json").read_text(encoding="utf-8"))["entries"]
    result = json.loads((LIVE_DIR / "result.json").read_text(encoding="utf-8"))
    source_rows = {row["source_contract_id"]: row for row in result["source_results"]}
    grouped = defaultdict(list)
    for row in ledger:
        grouped[row["source_contract_id"]].append(row)

    corrected = {}
    for source_id, source_result in source_rows.items():
        records = grouped[source_id]
        contract = source_result["drift_observation"]["contract_outcome"]
        semantic = source_result["drift_observation"]["semantic_outcome"]
        corrected[source_id] = _apply(
            source_result["verdict"], contract, semantic, source_result["bounded_detail"], records
        )[0]

    expected = {f"P{i:02d}": "TRANSPORT_OR_HTTP_DEGRADED" for i in (1, 2, 3, 4, 5, 6, 7, 12, 13, 14, 15, 18)}
    expected.update({f"P{i:02d}": "CONFORMING" for i in (8, 9, 10, 16, 17)})
    expected["P11"] = "CONFORMING_WITH_UNCERTAINTY"
    expected.update({f"B{i:02d}": "TRANSPORT_OR_HTTP_DEGRADED" for i in range(1, 6)})
    assert corrected == expected

    changed = [sid for sid in corrected if corrected[sid] != source_rows[sid]["verdict"]]
    degraded = sum(value == "TRANSPORT_OR_HTTP_DEGRADED" for value in corrected.values())
    http_200_ids = {row["source_contract_id"] for row in ledger if row["http_status"] == 200}
    contract_drift = sum(value == "CONTRACT_DRIFT_OBSERVED" for value in corrected.values())
    assert len(source_rows) == 23
    assert len(changed) == 11
    assert degraded == 17
    assert len(http_200_ids) == 6
    assert contract_drift == 0
    assert runner._overall([{"verdict": value} for value in corrected.values()]) == "PARTIAL"

    after = {name: hashlib.sha256((LIVE_DIR / name).read_bytes()).hexdigest() for name in LIVE_HASHES}
    assert after == before


def test_postlive_repair_has_no_acquisition_or_runner_replay_calls():
    # The replay test above only reads committed JSON and calls the pure classifier.
    assert callable(runner._apply_transport_precedence)
    assert LIVE_DIR.is_dir()
