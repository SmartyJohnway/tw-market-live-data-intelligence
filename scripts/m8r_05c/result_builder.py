"""Pure result builder for M8R-05C.

Assembles the complete AI-context result from all projection components.

This module:
- Is a pure function: no I/O, no network, no datetime.now().
- Delegates I/O to artifact_loader.py.
- Delegates lineage resolution to lineage_resolver.py.
- Delegates evidence projection to evidence_projector.py.
- Delegates derived metrics to derived_metrics.py.
- Delegates citations to citation_builder.py.
- Applies deterministic status rules.
- Produces a valid unified_market_evidence_result.v1 dict.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

from .canonical import (
    build_audit_package_id,
    build_result_id,
    hash_body_excluding_key,
)
from .citation_builder import CitationIndex, build_citation_index, get_citations_for_target
from .derived_metrics import project_derived_metrics
from .errors import ProjectionError
from .evidence_projector import CURRENT_PROJECTOR_VERSION, project_target_evidence
from .lineage_resolver import build_lineage_map
from .models import (
    CitationProjection,
    EvidenceEnvelopeProjection,
    PartialFailureProjection,
    ProjectionInputs,
    RequestSummaryProjection,
    ResolutionProjection,
    TargetProjection,
)

ROOT = Path(__file__).resolve().parents[2]
RESULT_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_result.v1.schema.json"
AUDIT_PACKAGE_RELATIVE_PATH = "audit/unified_market_evidence_audit_package.v1.json"
RESULT_RELATIVE_PATH = "ai_context/unified_market_evidence_result.v1.json"

_PROJECTOR_VERSION = "m8r_05c_v1"
_CANONICALIZATION_VERSION = "m8r_05b_03_canonical_v1"


def _load_result_schema() -> dict:
    try:
        return json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError("result_schema_load_failed") from exc


def _build_request_summary(request: dict) -> RequestSummaryProjection:
    data_needs = request.get("data_needs", [])
    requested = sorted(dn["type"] for dn in data_needs if isinstance(dn, dict) and "type" in dn)
    required = sorted(
        dn["type"] for dn in data_needs
        if isinstance(dn, dict) and dn.get("priority") == "required"
    )
    optional = sorted(
        dn["type"] for dn in data_needs
        if isinstance(dn, dict) and dn.get("priority") == "optional"
    )
    return RequestSummaryProjection(
        execution_mode=request.get("execution_mode"),
        target_count=len(request.get("targets", [])),
        requested_data_needs=requested,
        required_data_needs=required,
        optional_data_needs=optional,
    )


def _build_resolution(
    target_res,
    target_bindings: dict,
) -> ResolutionProjection:
    """Resolve status from lineage. Inherit F3 canonically resolved status."""
    status = target_res.resolution_status if target_res else "not_found"
    canonical_target_id = target_res.canonical_target_id if target_res else None
    market = target_res.market if target_res else None
    
    if not market and target_bindings:
        # Use the first binding to get market info if missing from F3.
        sample = next(iter(target_bindings.values()))
        market = sample.market
        
    return ResolutionProjection(
        status=status,
        canonical_target_id=canonical_target_id,
        market=market,
    )


def _compute_result_status(
    targets: list[TargetProjection],
    partial_failures: list,
    *,
    projector_version: str = CURRENT_PROJECTOR_VERSION,
) -> str:
    """Deterministic status mapping.

    full_success: all targets resolved, all required evidence present, no failures.
    success_with_partial_coverage: some optional evidence missing, no failures in required.
    partially_failed: some operations failed but at least one target has evidence.
    failed: all targets unresolved or all required evidence missing.
    """
    if not targets:
        return "failed"

    resolved_count = sum(1 for t in targets if t.resolution.status == "resolved")
    if resolved_count == 0:
        return "failed"

    if partial_failures:
        if projector_version != CURRENT_PROJECTOR_VERSION:
            return "partially_failed"
        # Identity resolution is not evidence success.  A required failure is
        # partial only when the canonical projection retained requested
        # evidence for at least one target; otherwise all required evidence is
        # missing and the Result is failed.
        has_provided_evidence = any(
            bool(target.coverage_provided_needs)
            for target in targets
        )
        return "partially_failed" if has_provided_evidence else "failed"

    # Check optional coverage gaps.
    has_optional_gap = any(t.coverage_missing_needs for t in targets)
    if has_optional_gap:
        return "success_with_partial_coverage"

    return "full_success"


def _envelope_to_dict(env: EvidenceEnvelopeProjection | None) -> dict | None:
    if env is None:
        return None
    d: dict = {"status": env.status}
    if env.timing_class is not None:
        d["timing_class"] = env.timing_class
    if env.caveats:
        d["caveats"] = env.caveats
    if env.observed_fields:
        d["observed_fields"] = env.observed_fields
    if env.missing_fields:
        d["missing_fields"] = env.missing_fields
    if env.currentness:
        d["currentness"] = env.currentness
    if env.fallback:
        d["fallback"] = env.fallback
    if env.fallback_state is not None:
        d["fallback_state"] = env.fallback_state
    if env.citation_ids:
        d["citation_ids"] = env.citation_ids
    return d


def _citation_to_dict(c: CitationProjection) -> dict:
    d: dict = {
        "citation_id": c.citation_id,
        "source_family": c.source_family,
        "retrieved_at": c.retrieved_at,
        "artifact_reference": c.artifact_reference,
    }
    if c.source_contract_id:
        d["source_contract_id"] = c.source_contract_id
    if c.normalized_evidence_hash:
        d["normalized_evidence_hash"] = c.normalized_evidence_hash
    return d


def _derived_metric_to_dict(m) -> dict:
    d: dict = {
        "metric_id": m.metric_id,
        "metric_name": m.metric_name,
        "status": m.status,
    }
    for field in [
        "value", "unit", "method", "formula_or_definition", "window",
        "calculation_version", "calculated_at", "invalid_reason",
    ]:
        v = getattr(m, field, None)
        if v is not None:
            d[field] = v
    if m.input_evidence_references:
        d["input_evidence_references"] = m.input_evidence_references
    if m.caveats:
        d["caveats"] = m.caveats
    if m.citation_ids:
        d["citation_ids"] = m.citation_ids
    return d


def build_result(inputs: ProjectionInputs, *, projector_version: str = CURRENT_PROJECTOR_VERSION) -> dict:
    """Build the complete AI-context result dict.

    Pure function: no I/O (inputs already loaded), no network, no datetime.now().

    Returns the result dict ready for schema validation and file materialization.
    """
    request = inputs.request
    receipt = inputs.receipt
    bundle = inputs.bundle
    calculated_at = inputs.calculated_at

    # Validate required IDs.
    request_id = request.get("request_id")
    if not request_id:
        raise ProjectionError("request_id_missing")

    receipt_id = receipt.get("execution_receipt_id")
    if not receipt_id:
        raise ProjectionError("receipt_id_missing")

    bundle_id = bundle.get("bundle_id")
    if not bundle_id:
        raise ProjectionError("bundle_id_missing")

    # Build result_id and audit_package_id (no circular reference).
    result_id = build_result_id(request_id, receipt_id, bundle_id)
    audit_package_id = build_audit_package_id(result_id, bundle_id)

    # Build request summary.
    request_summary = _build_request_summary(request)

    # Build lineage map.
    lineage = build_lineage_map(inputs)

    # Build citation index.
    citation_index = build_citation_index(lineage, bundle)

    # Build request parameter lookup for derived metrics.
    request_parameters: dict[str, dict] = {}
    for dn in request.get("data_needs", []):
        if isinstance(dn, dict) and "type" in dn:
            request_parameters[dn["type"]] = dn.get("parameters") or {}

    # Resolve targets.
    requested_targets = request.get("targets", [])
    target_projections: list[TargetProjection] = []
    partial_failures: list[PartialFailureProjection] = []

    # Build mapping: request target index -> f3_validation resolution -> canonical_target_id -> plan operations -> bundle evidence.
    for target_idx, req_target in enumerate(requested_targets):
        client_ref = req_target.get("client_target_reference")

        target_res = lineage.target_resolutions.get(target_idx)
        if not target_res or target_res.resolution_status != "resolved" or not target_res.canonical_target_id:
            # Not found or not resolved by F3 validation
            status = target_res.resolution_status if target_res else "not_found"
            tp = TargetProjection(
                resolution=ResolutionProjection(status=status),
                client_target_reference=client_ref,
            )
            target_projections.append(tp)
            partial_failures.append(
                PartialFailureProjection(
                    target_index=target_idx,
                    reason=f"target_resolution_failed:{status}",
                    reason_code="target_resolution_failed",
                )
            )
            continue

        canonical_target_id = target_res.canonical_target_id
        target_bindings = lineage.bindings.get(canonical_target_id, {})

        # Build citation map for this target.
        citation_map: dict[str, list[str]] = {}
        for key, cit_ids in citation_index.target_need_citations.items():
            if key.startswith(f"{canonical_target_id}::"):
                citation_map[key] = cit_ids

        # Project evidence.
        evidence_proj = project_target_evidence(
            canonical_target_id=canonical_target_id,
            lineage=lineage,
            requested_data_needs=request_summary.requested_data_needs,
            citation_map=citation_map, projector_version=projector_version,
        )

        # Project derived metrics.
        derived = project_derived_metrics(
            canonical_target_id=canonical_target_id,
            requested_data_needs=request_summary.requested_data_needs,
            target_bindings=target_bindings,
            calculated_at=calculated_at,
            citation_map=citation_map,
            request_parameters=request_parameters,
            enable_plan_only_reason=projector_version == CURRENT_PROJECTOR_VERSION,
        )

        # Compute coverage.
        provided_needs: list[str] = []
        missing_needs: list[str] = []
        for need in request_summary.requested_data_needs:
            binding = target_bindings.get(need)
            is_provided = False
            if binding and binding.status == "succeeded":
                # Ensure evidence was actually projected, or it's an artifact-free contract
                if getattr(evidence_proj, need, None) is not None:
                    is_provided = True
                elif not binding.evidence_artifacts:
                    is_provided = True
            
            if is_provided:
                provided_needs.append(need)
            else:
                missing_needs.append(need)
                if need in request_summary.required_data_needs:
                    partial_failures.append(
                        PartialFailureProjection(
                            target_index=target_idx,
                            reason=f"required_evidence_missing:{need}",
                            data_need=need,
                            reason_code="required_evidence_missing",
                        )
                    )

        # Build resolution.
        resolution = _build_resolution(target_res, target_bindings)

        # Collect used citation IDs for this target.
        used_cits: set[str] = set()
        for ev_field in [
            evidence_proj.identity,
            evidence_proj.current_observation,
            evidence_proj.recent_performance,
            evidence_proj.session_status,
            evidence_proj.source_currentness,
            evidence_proj.evidence_quality,
        ]:
            if ev_field and ev_field.citation_ids:
                used_cits.update(ev_field.citation_ids)
        for dm in derived:
            used_cits.update(dm.citation_ids)

        citations = get_citations_for_target(citation_index, canonical_target_id, used_cits)

        tp = TargetProjection(
            resolution=resolution,
            evidence=evidence_proj,
            derived_metrics=derived,
            coverage_provided_needs=sorted(provided_needs),
            coverage_missing_needs=sorted(missing_needs),
            caveats=[],
            citations=citations,
            client_target_reference=client_ref,
        )
        target_projections.append(tp)

    # Compute overall status.
    result_status = _compute_result_status(
        target_projections,
        partial_failures,
        projector_version=projector_version,
    )

    # Serialize targets to dicts.
    targets_dicts: list[dict] = []
    for tp in target_projections:
        t_dict: dict = {
            "resolution": {
                "status": tp.resolution.status,
            },
            "evidence": {},
        }
        if tp.client_target_reference is not None:
            t_dict["client_target_reference"] = tp.client_target_reference
        # Resolution fields.
        res = tp.resolution
        if res.canonical_target_id is not None:
            t_dict["resolution"]["canonical_target_id"] = res.canonical_target_id
        if res.security_code is not None:
            t_dict["resolution"]["security_code"] = res.security_code
        if res.security_name is not None:
            t_dict["resolution"]["security_name"] = res.security_name
        if res.market is not None:
            t_dict["resolution"]["market"] = res.market

        # Evidence fields.
        ev = tp.evidence
        for field_name, env_val in [
            ("identity", ev.identity),
            ("current_observation", ev.current_observation),
            ("recent_performance", ev.recent_performance),
            ("session_status", ev.session_status),
            ("source_currentness", ev.source_currentness),
            ("evidence_quality", ev.evidence_quality),
        ]:
            d = _envelope_to_dict(env_val)
            if d is not None:
                t_dict["evidence"][field_name] = d

        if ev.official_eod_reference is not None:
            t_dict["evidence"]["official_eod_reference"] = ev.official_eod_reference

        # Derived metrics.
        if tp.derived_metrics:
            t_dict["derived_metrics"] = [_derived_metric_to_dict(m) for m in tp.derived_metrics]

        # Coverage.
        coverage: dict = {}
        if tp.coverage_provided_needs is not None:
            coverage["provided_needs"] = tp.coverage_provided_needs
        if tp.coverage_missing_needs is not None:
            coverage["missing_needs"] = tp.coverage_missing_needs
        if coverage:
            t_dict["coverage"] = coverage

        if tp.caveats:
            t_dict["caveats"] = tp.caveats

        if tp.citations:
            t_dict["citations"] = [_citation_to_dict(c) for c in tp.citations]

        targets_dicts.append(t_dict)

    # Build partial_failures list.
    pf_dicts = []
    for pf in partial_failures:
        d: dict = {
            "target_index": pf.target_index,
            "reason": pf.reason,
        }
        if pf.data_need is not None:
            d["data_need"] = pf.data_need
        if pf.reason_code is not None:
            d["reason_code"] = pf.reason_code
        pf_dicts.append(d)

    # Build request_summary dict.
    rs_dict: dict = {
        "target_count": request_summary.target_count,
        "requested_data_needs": request_summary.requested_data_needs,
        "required_data_needs": request_summary.required_data_needs,
        "optional_data_needs": request_summary.optional_data_needs,
    }
    if request_summary.execution_mode is not None:
        rs_dict["execution_mode"] = request_summary.execution_mode

    # Build body without result_hash.
    body_without_hash: dict = {
        "schema_version": "unified_market_evidence_result.v1",
        "result_id": result_id,
        "request_id": request_id,
        "generated_at": calculated_at,
        "request_summary": rs_dict,
        "status": result_status,
        "targets": targets_dicts,
        "audit_reference": {
            "audit_package_id": audit_package_id,
            "schema_version": "unified_market_evidence_audit_package.v1",
            "relative_path": AUDIT_PACKAGE_RELATIVE_PATH,
        },
    }
    if pf_dicts:
        body_without_hash["partial_failures"] = pf_dicts
    body_without_hash["request_caveats"] = []

    # Compute result_hash.
    result_hash = hash_body_excluding_key(body_without_hash, "result_hash")
    result = {**body_without_hash, "result_hash": result_hash}

    # Validate against schema.
    schema = _load_result_schema()
    errors = list(Draft7Validator(schema).iter_errors(result))
    if errors:
        error_msgs = [str(e.message) for e in errors[:3]]
        raise ProjectionError(f"result_schema_invalid:{'; '.join(error_msgs)}")

    return result
