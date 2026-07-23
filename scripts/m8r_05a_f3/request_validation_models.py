"""Stable F3 constants; deliberately free of routing or execution concepts."""

OUTPUT_SCHEMA_VERSION = "unified_market_evidence_request_validation.v1"
TARGET_STATUSES = ("resolved", "ambiguous", "not_found", "market_mismatch", "unsupported_market", "invalid_market_hint", "unsupported_security_type", "invalid_input", "duplicate", "quarantined")
CAPABILITY_STATUSES = ("contract_supported", "runtime_executable", "provisional", "unsupported", "requires_target_resolution", "invalid_parameters", "unknown")
REASON_SECURITY_TYPE_UNSUPPORTED = "TARGET_SECURITY_TYPE_UNSUPPORTED"
REASON_IDENTITY_QUARANTINED = "TARGET_IDENTITY_QUARANTINED"
REASON_DUPLICATE = "TARGET_DUPLICATE_CANONICAL_IDENTITY"
REASON_FIXTURE_REJECTED = "TARGET_FIXTURE_OBSERVATION_REJECTED"
UNSUPPORTED_SECURITY_REASON_CODES = frozenset({"unsupported_instrument_type", "unsupported_instrument_family", "instrument_type_not_runtime_supported", "security_type_not_supported"})
TARGET_BLOCKER_BY_STATUS = {"invalid_input":"REQUIRED_TARGET_INVALID_INPUT", "not_found":"REQUIRED_TARGET_NOT_FOUND", "market_mismatch":"REQUIRED_TARGET_MARKET_MISMATCH", "invalid_market_hint":"REQUIRED_TARGET_INVALID_MARKET_HINT", "duplicate":"REQUIRED_TARGET_DUPLICATE", "ambiguous":"REQUIRED_TARGET_AMBIGUOUS", "unsupported_market":"REQUIRED_TARGET_UNSUPPORTED_MARKET", "unsupported_security_type":"REQUIRED_TARGET_SECURITY_TYPE_UNSUPPORTED", "quarantined":"REQUIRED_TARGET_QUARANTINED"}
