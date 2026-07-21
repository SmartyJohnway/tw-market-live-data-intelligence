from typing import TypedDict, List, Optional, Any, Dict, Literal

# Reason Code Constants
REQUEST_SCHEMA_INVALID = "REQUEST_SCHEMA_INVALID"
UNSUPPORTED_SCHEMA_VERSION = "UNSUPPORTED_SCHEMA_VERSION"
TARGET_INPUT_EMPTY = "TARGET_INPUT_EMPTY"
TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
TARGET_AMBIGUOUS = "TARGET_AMBIGUOUS"
TARGET_MARKET_MISMATCH = "TARGET_MARKET_MISMATCH"
TARGET_MARKET_UNSUPPORTED = "TARGET_MARKET_UNSUPPORTED"
TARGET_SECURITY_TYPE_UNSUPPORTED = "TARGET_SECURITY_TYPE_UNSUPPORTED"
TARGET_DUPLICATE = "TARGET_DUPLICATE"
MARKET_HINT_INVALID = "MARKET_HINT_INVALID"
CAPABILITY_UNKNOWN = "CAPABILITY_UNKNOWN"
CAPABILITY_UNSUPPORTED_FOR_MARKET = "CAPABILITY_UNSUPPORTED_FOR_MARKET"
CAPABILITY_PARAMETER_INVALID = "CAPABILITY_PARAMETER_INVALID"
TARGET_LIMIT_EXCEEDED = "TARGET_LIMIT_EXCEEDED"
REQUIRED_TARGET_UNRESOLVED = "REQUIRED_TARGET_UNRESOLVED"
REQUIRED_CAPABILITY_UNAVAILABLE = "REQUIRED_CAPABILITY_UNAVAILABLE"


class CanonicalIdentity(TypedDict):
    security_code: str
    market: str
    security_name_zh: str
    security_name_en: Optional[str]
    security_type: str
    listing_status: Optional[str]
    effective_from: Optional[str]
    effective_to: Optional[str]
    identity_source: Optional[str]
    identity_record_reference: Optional[str]


class TargetResult(TypedDict):
    target_index: int
    original_input: str
    market_hint: Optional[str]
    resolution_requirement: str
    resolution_status: str
    canonical_identity: Optional[CanonicalIdentity]
    candidate_matches: List[Dict[str, Any]]
    reason_codes: List[str]
    evidence_references: List[str]


class CapabilityResult(TypedDict):
    type: str
    priority: str
    status: str
    supported_markets: List[str]
    reason_codes: List[str]


class BlockingIssue(TypedDict):
    reason_code: str
    json_path: str
    schema_path: str
    message: str


class WarningIssue(TypedDict):
    reason_code: str
    message: str


class Limits(TypedDict):
    target_count: int
    data_need_count: int
    operation_count_computed: bool
    operation_count: int
    orchestrator_projection_required: bool


class UnifiedMarketEvidenceRequestValidation(TypedDict):
    schema_version: str
    request_id: str
    validation_status: str
    request_schema_status: str
    capability_validation_status: str
    target_validation_status: str
    normalized_request: Dict[str, Any]
    target_results: List[TargetResult]
    capability_results: List[CapabilityResult]
    blocking_issues: List[BlockingIssue]
    warnings: List[WarningIssue]
    limits: Limits
    validation_metadata: Dict[str, Any]
