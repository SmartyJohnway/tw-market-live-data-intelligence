"""Stable F3 constants; deliberately free of routing or execution concepts."""

OUTPUT_SCHEMA_VERSION = "unified_market_evidence_request_validation.v1"
TARGET_STATUSES = ("resolved", "ambiguous", "not_found", "market_mismatch", "unsupported_market", "invalid_market_hint", "unsupported_security_type", "invalid_input", "duplicate", "quarantined")
CAPABILITY_STATUSES = ("contract_supported", "runtime_executable", "provisional", "unsupported", "requires_target_resolution", "invalid_parameters", "unknown")
REASON_SECURITY_TYPE_UNSUPPORTED = "TARGET_SECURITY_TYPE_UNSUPPORTED"
REASON_IDENTITY_QUARANTINED = "TARGET_IDENTITY_QUARANTINED"
REASON_DUPLICATE = "TARGET_DUPLICATE_CANONICAL_IDENTITY"
REASON_FIXTURE_REJECTED = "TARGET_FIXTURE_OBSERVATION_REJECTED"
