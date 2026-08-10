import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMA_DIR = Path(__file__).parent.parent.parent / "schemas"

@pytest.fixture(scope="module")
def preview_schema():
    with open(SCHEMA_DIR / "unified_market_evidence_preview_response.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def result_schema():
    with open(SCHEMA_DIR / "unified_market_evidence_result.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Preview Fixtures

def test_valid_preview_ready_for_confirmation(preview_schema):
    preview = {
        "schema_version": "unified_market_evidence_preview_response.v1",
        "request_id": "req-001",
        "status": "ready_for_confirmation",
        "target_resolution_summary": {
            "resolved": ["2330"],
            "ambiguous": [],
            "not_found": []
        },
        "requested_data_needs": ["current_observation", "official_eod_reference"],
        "planned_evidence": ["current_observation", "official_eod_reference"],
        "coverage_expectation": {
            "status": "full_possible",
            "known_gaps": []
        },
        "bounds": {
            "target_count": 1,
            "operation_count": 2,
            "estimated_network_calls": 2,
            "expanded_scope": False
        },
        "fallbacks": [],
        "approval": {
            "required": True,
            "confirmation_text": "Proceed to fetch data?"
        },
        "internal_execution_reference": {
            "preview_id": "preview-123"
        },
        "caveats": []
    }
    validate(instance=preview, schema=preview_schema)

def test_valid_preview_partial_possible(preview_schema):
    preview = {
        "schema_version": "unified_market_evidence_preview_response.v1",
        "request_id": "req-001",
        "status": "partial_possible",
        "target_resolution_summary": {
            "resolved": ["2330"],
            "ambiguous": [],
            "not_found": []
        },
        "requested_data_needs": ["current_observation", "recent_performance"],
        "planned_evidence": ["current_observation"],
        "coverage_expectation": {
            "status": "partial_possible",
            "known_gaps": ["recent_performance not yet implemented"]
        },
        "bounds": {
            "target_count": 1,
            "operation_count": 1,
            "estimated_network_calls": 1,
            "expanded_scope": False
        },
        "fallbacks": [],
        "approval": {
            "required": True,
            "confirmation_text": "Proceed with partial data?"
        },
        "caveats": ["recent_performance will be omitted"]
    }
    validate(instance=preview, schema=preview_schema)


def _target_outcome_preview(status, summary_field):
    summary = {
        "resolved": [],
        "ambiguous": [],
        "not_found": [],
        "market_hint_conflict": [],
        "unsupported_market": [],
        "invalid_market_hint": [],
        "unsupported_security_type": [],
        "invalid_input": [],
        "duplicate": [],
        "quarantined": [],
    }
    summary[summary_field] = ["target-1"]
    return {
        "schema_version": "unified_market_evidence_preview_response.v1",
        "request_id": "req-target-outcome",
        "status": status,
        "target_resolution_summary": summary,
        "requested_data_needs": ["current_observation"],
        "planned_evidence": [],
        "coverage_expectation": {
            "status": "none_possible",
            "known_gaps": [summary_field],
        },
        "bounds": {
            "target_count": 1,
            "operation_count": 0,
            "estimated_network_calls": 0,
            "expanded_scope": False,
        },
        "fallbacks": [],
        "approval": {
            "required": False,
            "confirmation_text": "Preview only; target is not plannable.",
        },
        "caveats": ["No execution is authorized."],
    }


@pytest.mark.parametrize(
    "summary_field",
    [
        "not_found",
        "market_hint_conflict",
        "unsupported_market",
        "invalid_market_hint",
        "unsupported_security_type",
        "invalid_input",
        "duplicate",
        "quarantined",
    ],
)
def test_target_not_plannable_outcomes_are_valid(preview_schema, summary_field):
    validate(
        instance=_target_outcome_preview("target_not_plannable", summary_field),
        schema=preview_schema,
    )


def test_ambiguous_target_remains_a_distinct_valid_status(preview_schema):
    validate(
        instance=_target_outcome_preview("ambiguous_target", "ambiguous"),
        schema=preview_schema,
    )

# Result Fixtures

def test_valid_result_full_success(result_schema):
    result = {
        "schema_version": "unified_market_evidence_result.v1",
        "result_id": "umeresult-v1-00000000000000000000",
        "result_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "generated_at": "2026-07-20T12:00:00Z",
        "request_id": "req-001",
        "request_summary": {
            "execution_mode": "latest_published",
            "target_count": 1,
            "requested_data_needs": ["official_eod_reference"],
            "required_data_needs": ["official_eod_reference"],
            "optional_data_needs": []
        },
        "status": "full_success",
        "targets": [
            {
                "client_target_reference": "target-1",
                "resolution": {
                    "status": "resolved",
                    "canonical_target_id": "TWSE:2330",
                    "security_code": "2330",
                    "security_name": "台積電",
                    "market": "TWSE"
                },
                "evidence": {
                    "official_eod_reference": {
                        "trade_date": "2026-07-17",
                        "expected_latest_completed_trade_date": "2026-07-17",
                        "currentness_status": "official_latest_completed_eod",
                        "session_status": "regular_trading_day",
                        "publication_grace_applied": False,
                        "fallback_policy_used": False,
                        "provisional_candidate_status": None,
                        "caveats": []
                    }
                },
                "coverage": {},
                "caveats": [],
                "citations": [
                    {
                        "citation_id": "cite-1",
                        "source_family": "twse_openapi",
                        "source_contract_id": "03e-twse-eod",
                        "retrieved_at": "2026-07-20T12:00:00Z",
                        "effective_trade_date": "2026-07-17",
                        "artifact_reference": "artifact-123",
                        "normalized_evidence_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
                    }
                ]
            }
        ],
        "audit_reference": {
            "audit_package_id": "umeap-v1-00000000000000000000",
            "schema_version": "unified_market_evidence_audit_package.v1",
            "relative_path": "audit/unified_market_evidence_audit_package.v1.json"
        }
    }
    validate(instance=result, schema=result_schema)

def test_valid_result_not_yet_published(result_schema):
    result = {
        "schema_version": "unified_market_evidence_result.v1",
        "result_id": "umeresult-v1-11111111111111111111",
        "result_hash": "1111111111111111111111111111111111111111111111111111111111111111",
        "generated_at": "2026-07-20T12:00:00Z",
        "request_id": "req-001",
        "request_summary": {
            "execution_mode": "latest_published",
            "target_count": 1,
            "requested_data_needs": ["official_eod_reference"],
            "required_data_needs": ["official_eod_reference"],
            "optional_data_needs": []
        },
        "status": "success_with_partial_coverage",
        "targets": [
            {
                "client_target_reference": "target-1",
                "resolution": {
                    "status": "resolved",
                    "canonical_target_id": "TWSE:2330"
                },
                "evidence": {
                    "official_eod_reference": {
                        "trade_date": "2026-07-16",
                        "expected_latest_completed_trade_date": "2026-07-17",
                        "currentness_status": "not_yet_published_after_close",
                        "session_status": "regular_trading_day",
                        "publication_grace_applied": True,
                        "fallback_policy_used": True,
                        "provisional_candidate_status": None,
                        "caveats": ["Fallback to T-1"]
                    }
                },
                "coverage": {},
                "caveats": [],
                "citations": []
            }
        ],
        "audit_reference": {
            "audit_package_id": "umeap-v1-11111111111111111111",
            "schema_version": "unified_market_evidence_audit_package.v1",
            "relative_path": "audit/unified_market_evidence_audit_package.v1.json"
        }
    }
    validate(instance=result, schema=result_schema)

def test_invalid_result_pre_05c_migration(result_schema):
    """
    Explicit compatibility test showing that pre-05C incomplete payloads
    fail validation after the v1 schema was intentionally completed.
    This proves that downstream consumers must migrate to the completed shape.
    """
    result = {
        "schema_version": "unified_market_evidence_result.v1",
        "request_id": "req-001",
        "status": "full_success",
        "targets": []
    }
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=result, schema=result_schema)
    
    msg = str(exc_info.value)
    assert "result_id" in msg or "result_hash" in msg or "generated_at" in msg or "request_summary" in msg


# Negative Result Fixture (raw payload disallowed implicitly by strict schemas, no unknown properties)
def test_invalid_result_has_raw_payload(result_schema):
    result = {
        "schema_version": "unified_market_evidence_result.v1",
        "request_id": "req-001",
        "status": "full_success",
        "targets": [],
        "raw_payload": {"data": "some internal data"}  # Prohibited
    }
    with pytest.raises(ValidationError):
        validate(instance=result, schema=result_schema)
