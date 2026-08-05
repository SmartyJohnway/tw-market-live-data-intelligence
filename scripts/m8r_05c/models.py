"""Pure dataclasses for M8R-05C projection layer.

All fields are built from the accepted 05B-03 execution artifacts.
No network access.  No side effects.  No datetime.now() calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvidenceEnvelopeProjection:
    status: str
    timing_class: str | None = None
    caveats: list[str] = field(default_factory=list)
    observed_fields: dict = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    currentness: dict = field(default_factory=dict)
    fallback: bool = False
    fallback_state: str | None = None
    citation_ids: list[str] = field(default_factory=list)


@dataclass
class DerivedMetricProjection:
    metric_id: str
    metric_name: str
    status: str  # available | unavailable | invalid | not_requested
    value: float | str | None = None
    unit: str | None = None
    method: str | None = None
    formula_or_definition: str | None = None
    window: str | None = None
    input_evidence_references: list[str] = field(default_factory=list)
    calculation_version: str | None = None
    calculated_at: str | None = None
    invalid_reason: str | None = None
    caveats: list[str] = field(default_factory=list)
    citation_ids: list[str] = field(default_factory=list)


@dataclass
class CitationProjection:
    citation_id: str
    source_family: str
    retrieved_at: str
    artifact_reference: str  # relative path only — never absolute
    source_contract_id: str | None = None
    effective_trade_date: str | None = None
    normalized_evidence_hash: str | None = None


@dataclass
class ResolutionProjection:
    status: str  # resolved | ambiguous | not_found | market_hint_conflict | unsupported_market
    canonical_target_id: str | None = None
    security_code: str | None = None
    security_name: str | None = None
    market: str | None = None


@dataclass
class TargetEvidenceProjection:
    identity: EvidenceEnvelopeProjection | None = None
    current_observation: EvidenceEnvelopeProjection | None = None
    official_eod_reference: dict | None = None
    recent_performance: EvidenceEnvelopeProjection | None = None
    session_status: EvidenceEnvelopeProjection | None = None
    source_currentness: EvidenceEnvelopeProjection | None = None
    evidence_quality: EvidenceEnvelopeProjection | None = None


@dataclass
class TargetProjection:
    resolution: ResolutionProjection
    evidence: TargetEvidenceProjection = field(default_factory=TargetEvidenceProjection)
    derived_metrics: list[DerivedMetricProjection] = field(default_factory=list)
    coverage_provided_needs: list[str] = field(default_factory=list)
    coverage_missing_needs: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    citations: list[CitationProjection] = field(default_factory=list)
    client_target_reference: str | None = None


@dataclass
class PartialFailureProjection:
    target_index: int
    reason: str
    data_need: str | None = None
    reason_code: str | None = None


@dataclass
class RequestSummaryProjection:
    target_count: int
    requested_data_needs: list[str]
    required_data_needs: list[str]
    optional_data_needs: list[str]
    execution_mode: str | None = None


@dataclass
class ProjectionInputs:
    """All accepted M8R-05B-03 artifacts consumed as inputs by 05C.

    Fields are populated by artifact_loader.py.  All dicts are the
    deserialized JSON objects (validated against their schemas).
    """
    request: dict
    f3_validation: dict
    plan: dict
    authorization: dict
    consumption_binding: dict
    receipt: dict
    bundle: dict
    artifact_root: str  # governed output_root used during 05B-03 execution
    calculated_at: str  # ISO-8601 UTC datetime from CLI or receipt.finalized_at
    # Loaded evidence artifact JSON objects keyed by relative_path
    evidence_artifacts: dict[str, dict] = field(default_factory=dict)


@dataclass
class ProjectionResult:
    """Complete deterministic projection output."""
    result_id: str
    result_hash: str
    request_id: str
    generated_at: str
    request_summary: RequestSummaryProjection
    status: str  # full_success | success_with_partial_coverage | failed | partially_failed
    targets: list[TargetProjection]
    partial_failures: list[PartialFailureProjection]
    request_caveats: list[str]
    audit_package_id: str
    # For the audit package (built separately, not embedded in result)
    audit_relative_path: str


@dataclass
class CitationToOperationEntry:
    citation_id: str
    operation_id: str
    capability_id: str
    executor_id: str
    artifact_relative_path: str
    artifact_hash: str
    canonical_target_id: str
    requested_data_need: str
