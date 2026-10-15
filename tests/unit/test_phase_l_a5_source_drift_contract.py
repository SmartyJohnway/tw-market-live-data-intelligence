from __future__ import annotations

import socket
import urllib.request

import pytest

from server.services.phase_l_source_drift_contract import (
    MAX_RETRY_AFTER_DELTA_SECONDS,
    observe_source_attempt,
    parse_retry_after,
)


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    """The contract is offline; any external connection/API attempt fails the test."""
    attempts: list[str] = []

    def reject(*args, **kwargs):
        attempts.append("external_network_attempt")
        raise AssertionError("A5 must not access the network")

    monkeypatch.setattr(socket, "create_connection", reject)
    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket.socket, "connect_ex", reject)
    monkeypatch.setattr(urllib.request, "urlopen", reject)
    yield
    assert attempts == []


@pytest.mark.parametrize(
    ("value", "kind", "seconds", "date"),
    [
        (None, "absent", None, None),
        ("0", "delta_seconds", 0, None),
        ("120", "delta_seconds", 120, None),
        ("Tue, 15 Nov 1994 08:12:31 GMT", "http_date", None, "Tue, 15 Nov 1994 08:12:31 GMT"),
        ("bad", "invalid", None, None),
        ("-1", "invalid", None, None),
        ("1.5", "invalid", None, None),
        (str(MAX_RETRY_AFTER_DELTA_SECONDS + 1), "out_of_range", None, None),
    ],
)
def test_retry_after_is_bounded_fact_only(value, kind, seconds, date):
    fact = parse_retry_after(value)
    assert fact.kind == kind
    assert fact.present is (value is not None)
    assert fact.delta_seconds == seconds
    assert fact.http_date == date


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (200, "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
        (429, "HTTP_FAILURE_REPORTED"),
        (404, "HTTP_FAILURE_REPORTED"),
        (410, "HTTP_FAILURE_REPORTED"),
        (503, "HTTP_FAILURE_REPORTED"),
    ],
)
def test_http_status_is_observed_without_source_retirement_inference(status, expected):
    result = observe_source_attempt(
        source_contract_id="P02:TWSE_OPENAPI", observed_at="2026-10-15T00:00:00Z",
        http_status=status, retry_after="60",
    )
    assert result.adjudication == expected
    facts = set(result.drift_observations)
    if status == 429:
        assert "rate_limit_observed" in facts
    if status == 404:
        assert "endpoint_not_found_observed" in facts
        assert "source_removed" not in facts
    if status == 410:
        assert "endpoint_gone_observed" in facts
        assert "source_authority_retired" not in facts


def test_retry_after_never_changes_outcome_into_schedule_or_retry():
    result = observe_source_attempt(
        source_contract_id="P02:TWSE_OPENAPI", observed_at="2026-10-15T00:00:00Z",
        http_status=429, retry_after="60",
    ).as_dict()
    assert result["retry_after"] == {"present": True, "kind": "delta_seconds", "delta_seconds": 60, "http_date": None}
    assert not {"sleep", "retry", "schedule_next_run", "retry_count"}.intersection(result)


def test_429_with_malformed_retry_after_remains_observation_only():
    result = observe_source_attempt(
        source_contract_id="P01:TWSE_MIS", observed_at="2026-10-15T00:00:00Z",
        http_status=429, retry_after="-30",
    )
    assert "rate_limit_observed" in result.drift_observations
    assert "retry_after_unparseable" in result.drift_observations
    assert result.adjudication == "HTTP_FAILURE_REPORTED"


def test_arbitrary_deprecation_text_is_not_a_lifecycle_signal():
    # The observation API has no body/text argument, so provider prose cannot
    # be interpreted as a source-authority or deprecation conclusion.
    result = observe_source_attempt(
        source_contract_id="P04:MOPS_MATERIAL_DISCLOSURE_OPEN_DATA:t187ap04_L",
        observed_at="2026-10-15T00:00:00Z", http_status=200,
    )
    assert "explicit_deprecation_signal_observed" not in result.drift_observations
    assert result.adjudication == "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"


@pytest.mark.parametrize(
    ("semantic", "expected_fact"),
    [
        ("not_yet_available", "publication_delay_observed"),
        ("currentness_unknown", "currentness_unknown"),
        ("no_evidence_in_covered_scope", None),
        ("partial", None),
        ("missing", None),
        ("unavailable", None),
        ("stale", None),
    ],
)
def test_source_publication_and_currentness_semantics_are_preserved(semantic, expected_fact):
    result = observe_source_attempt(
        source_contract_id="P17:I3-TWSE-T86-INSTITUTIONAL-TRADING",
        observed_at="2026-10-15T00:00:00Z", http_status=200,
        semantic_outcome=semantic,
    )
    assert result.semantic_outcome == semantic
    assert result.adjudication == "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"
    if expected_fact:
        assert expected_fact in result.drift_observations
    assert "source_failed" not in result.drift_observations


def test_previous_period_does_not_become_current_or_stale_by_age_heuristic():
    result = observe_source_attempt(
        source_contract_id="P06:MOPS_MONTHLY_REVENUE_OPEN_DATA:t187ap05_L",
        observed_at="2026-10-15T00:00:00Z", http_status=200,
        semantic_outcome="available", source_reported_period="202608",
        requested_period="202609",
    )
    assert result.source_reported_period == "202608"
    assert result.requested_period == "202609"
    assert result.semantic_outcome == "available"
    assert result.adjudication == "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"
    assert "publication_delay_observed" not in result.drift_observations


def test_transport_timeout_stays_distinct_from_http_and_contract_failures():
    result = observe_source_attempt(
        source_contract_id="P12:H3-TWSE-DEFAULT-BOUNDED",
        observed_at="2026-10-15T00:00:00Z", http_status=None,
        transport_outcome="transport_failure",
    )
    assert result.http_status is None
    assert result.adjudication == "TRANSPORT_FAILURE_REPORTED"


@pytest.mark.parametrize(
    ("response_form", "policy", "expected"),
    [
        ("empty_body", "invalid", "SOURCE_CONTRACT_REJECTS_EMPTY_RESPONSE"),
        ("empty_collection", "allowed", "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
        ("empty_collection", "unknown", "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
        ("nonempty", "unknown", "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
    ],
)
def test_empty_response_requires_exact_source_policy(response_form, policy, expected):
    result = observe_source_attempt(
        source_contract_id="P02:TWSE_OPENAPI", observed_at="2026-10-15T00:00:00Z",
        http_status=200, response_form=response_form, empty_response_policy=policy,
        semantic_outcome="no_evidence_in_covered_scope",
    )
    assert result.adjudication == expected
    assert result.semantic_outcome == "no_evidence_in_covered_scope"


def test_contractual_selector_absence_is_contract_failure_not_universe_guess():
    result = observe_source_attempt(
        source_contract_id="P14:I1-TWSE-BREADTH-TWTAZU-OPENAPI",
        observed_at="2026-10-15T00:00:00Z", http_status=200,
        contract_outcome="invalid", semantic_outcome="partial",
    )
    assert result.adjudication == "CONTRACT_FAILURE_REPORTED"
    assert result.semantic_outcome == "partial"


@pytest.mark.parametrize(
    ("before", "after", "binding", "delta", "adjudication"),
    [
        (10, 12, "matched", 2, "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
        (12, 10, "matched", -2, "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
        (10, 10, "absent", 0, "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"),
        (10, 10, "ambiguous", 0, "SOURCE_SPECIFIC_TARGET_ADJUDICATION_REQUIRED"),
    ],
)
def test_row_count_delta_is_observation_not_universe_failure(before, after, binding, delta, adjudication):
    result = observe_source_attempt(
        source_contract_id="P14:I1-TWSE-BREADTH-TWTAZU-OPENAPI",
        observed_at="2026-10-15T00:00:00Z", http_status=200,
        previous_row_count=before, current_row_count=after, target_binding=binding,
    )
    assert result.observed_row_delta == delta
    assert result.adjudication == adjudication
    if delta:
        assert "observed_universe_delta" in result.drift_observations
    assert "source_universe_invalid" not in result.drift_observations


@pytest.mark.parametrize("binding", ["absent", "ambiguous"])
def test_target_absence_and_ambiguity_are_kept_separate(binding):
    result = observe_source_attempt(
        source_contract_id="P08:H1-TPEX-ATTENTION-OPENAPI",
        observed_at="2026-10-15T00:00:00Z", http_status=200,
        target_binding=binding,
    )
    assert "target_scope_change_observed" in result.drift_observations
    assert result.adjudication == (
        "SOURCE_SPECIFIC_TARGET_ADJUDICATION_REQUIRED" if binding == "ambiguous"
        else "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"
    )


def test_observation_retains_supplied_source_contract_identity():
    result = observe_source_attempt(
        source_contract_id="P01:TWSE_MIS",
        observed_at="2026-10-15T00:00:00Z", http_status=429,
        retry_after=None,
    )
    assert result.source_contract_id == "P01:TWSE_MIS"
    assert "rate_limit_observed" in result.drift_observations
    assert result.adjudication == "HTTP_FAILURE_REPORTED"


def test_invalid_facts_fail_closed_and_output_is_deterministic():
    kwargs = dict(
        source_contract_id="P03:TPEX_OPENAPI", observed_at="2026-10-15T00:00:00Z",
        http_status=200, previous_row_count=4, current_row_count=5,
    )
    assert observe_source_attempt(**kwargs).as_dict() == observe_source_attempt(**kwargs).as_dict()
    with pytest.raises(ValueError, match="semantic_outcome_invalid"):
        observe_source_attempt(**{**kwargs, "semantic_outcome": "looks_current"})
    with pytest.raises(ValueError, match="http_status_invalid"):
        observe_source_attempt(**{**kwargs, "http_status": 99})
