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
    build_audit_package_id_v2,
    build_result_id_v2,
    build_result_id_v3,
    build_audit_package_id_v3,
    hash_body_excluding_key,
)
from .citation_builder import CitationIndex, build_citation_index, get_citations_for_target
from .derived_metrics import project_derived_metrics
from .errors import ProjectionError
from .evidence_projector import (
    CURRENT_PROJECTOR_VERSION,
    project_target_evidence,
    project_phase_h_typed_evidence,
)
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
RESULT_V2_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_result.v2.schema.json"
RESULT_V3_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_result.v3.schema.json"
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
        request_schema_version=request.get("schema_version"),
    )


def _build_resolution(
    target_res,
    target_bindings: dict,
) -> ResolutionProjection:
    """Resolve status from lineage. Inherit F3 canonically resolved status."""
    status = target_res.resolution_status if target_res else "not_found"
    canonical_target_id = target_res.canonical_target_id if target_res else None
    market = target_res.market if target_res else None
    identity = target_res.canonical_identity if target_res else None
    
    if not market and target_bindings:
        # Use the first binding to get market info if missing from F3.
        sample = next(iter(target_bindings.values()))
        market = sample.market
        
    return ResolutionProjection(
        status=status,
        canonical_target_id=canonical_target_id,
        market=market,
        security_code=(identity or {}).get("security_code"),
        security_name=(identity or {}).get("security_name_zh"),
        canonical_identity=(identity.copy() if identity else None),
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
    if c.source_report_date:
        d["source_report_date"] = c.source_report_date
    return d


def _canonical_identity_v2(resolution: ResolutionProjection) -> dict | None:
    """Project only the frozen V2 identity vocabulary from governed F3 data."""
    identity = resolution.canonical_identity
    if identity is None:
        return None
    return {
        "canonical_target_id": identity.get("canonical_target_id", resolution.canonical_target_id),
        "isin": identity.get("isin"),
        "market": identity.get("market", resolution.market),
        "security_code": identity.get("security_code", resolution.security_code),
        "security_name_zh": identity.get("security_name_zh", resolution.security_name),
        "security_name_en": identity.get("security_name_en"),
        "instrument_family": identity.get("instrument_family"),
        "instrument_type": identity.get("instrument_type"),
    }


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


def _research_status(evidence, need: str) -> str | None:
    value = getattr(evidence, need, None)
    return value.get("status") if isinstance(value, dict) else None


def _not_applicable_research(need: str, observed_at: str, market: str | None) -> dict:
    if need == "material_disclosures":
        return {
            "schema_version": "material_disclosure_evidence.v1", "status": "not_applicable",
            "coverage": {"mode": "latest_completed_official_daily_batch", "source_report_date": None,
                         "coverage_through": None, "historical_lookup_supported": False,
                         "item_count": 0, "truncated": False},
            "currentness": {"status": "unknown", "observed_at": observed_at},
            "source": {"authority": "official", "source_family": "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA",
                       "market": market or "TWSE", "source_contract_id": "not_applicable",
                       "transport": "official_csv", "fallback_used": False},
            "items": [], "caveats": ["target_not_applicable_to_research_capability"], "citation_ids": [],
        }
    return {
        "schema_version": "monthly_revenue_evidence.v1", "status": "not_applicable",
        "coverage": {"mode": "latest_available_reporting_period", "reporting_period": None,
                     "source_report_date": None, "historical_lookup_supported": False},
        "currentness": {"status": "unknown", "observed_at": observed_at},
        "source": {"authority": "official", "source_family": "MOPS_MONTHLY_REVENUE_OPEN_DATA",
                   "market": market or "TWSE", "source_contract_id": "not_applicable",
                   "transport": "official_csv", "fallback_used": False},
        "value": None, "caveats": ["target_not_applicable_to_research_capability"], "citation_ids": [],
    }


def _derived_h4_artifact(inputs: ProjectionInputs, canonical_target_id: str) -> dict | None:
    """Find the one verified, target-scoped H4 artifact supplied to projection.

    H4 is derived evidence rather than a request capability, so it has no
    operation binding.  The hook remains local to projection and accepts only
    an artifact present in the already-verified bundle inventory.
    """
    inventory_paths = {
        entry.get("relative_path") for entry in inputs.bundle.get("artifact_inventory", [])
        if isinstance(entry, dict)
    }
    matches = []
    for path, artifact in inputs.evidence_artifacts.items():
        if not isinstance(artifact, dict) or path not in inventory_paths:
            continue
        if artifact.get("schema_version") != "discontinuity_safety_evidence.v1":
            continue
        target = artifact.get("target")
        if isinstance(target, dict) and target.get("canonical_target_id") == canonical_target_id:
            matches.append(artifact)
    if len(matches) > 1:
        raise ProjectionError("duplicate_phase_h_h4_artifact")
    return matches[0].copy() if matches else None


def build_result(inputs: ProjectionInputs, *, projector_version: str = CURRENT_PROJECTOR_VERSION,
                 output_schema_version: str = "unified_market_evidence_result.v1") -> dict:
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
    if output_schema_version == "unified_market_evidence_result.v1":
        result_id = build_result_id(request_id, receipt_id, bundle_id)
        audit_package_id = build_audit_package_id(result_id, bundle_id)
    elif output_schema_version == "unified_market_evidence_result.v2":
        result_id = build_result_id_v2(request_id, receipt_id, bundle_id)
        audit_package_id = build_audit_package_id_v2(result_id, bundle_id)
    elif output_schema_version == "unified_market_evidence_result.v3":
        result_id = build_result_id_v3(request_id, receipt_id, bundle_id)
        audit_package_id = build_audit_package_id_v3(result_id, bundle_id)
    else:
        raise ProjectionError("unsupported_output_schema_version")

    # Build request summary.
    request_summary = _build_request_summary(request)

    # Build lineage map.
    lineage = build_lineage_map(inputs)

    # Build citation index.
    citation_index = build_citation_index(lineage, bundle, output_schema_version)

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
        if output_schema_version == "unified_market_evidence_result.v3":
            evidence_proj.trading_status_context = project_phase_h_typed_evidence(
                target_bindings.get("trading_status_context"),
                citation_map.get(f"{canonical_target_id}::trading_status_context", []),
                "trading_status_context_evidence.v1",
            )
            evidence_proj.corporate_action_context = project_phase_h_typed_evidence(
                target_bindings.get("corporate_action_context"),
                citation_map.get(f"{canonical_target_id}::corporate_action_context", []),
                "corporate_action_context_evidence.v1",
            )
            evidence_proj.recent_performance_v3 = project_phase_h_typed_evidence(
                target_bindings.get("recent_performance"),
                citation_map.get(f"{canonical_target_id}::recent_performance", []),
                "recent_performance_evidence.v1",
            )
            evidence_proj.discontinuity_safety = _derived_h4_artifact(inputs, canonical_target_id)
        if output_schema_version.endswith(".v2"):
            identity = target_res.canonical_identity or {}
            applicable = (
                identity.get("instrument_family") == "company_share"
                and identity.get("instrument_type") == "common_share"
            )
            if not applicable:
                for research_need in ("material_disclosures", "monthly_revenue"):
                    if research_need in request_summary.requested_data_needs and not target_bindings.get(research_need):
                        setattr(evidence_proj, research_need, _not_applicable_research(
                            research_need, calculated_at, target_res.market,
                        ))

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
            if output_schema_version == "unified_market_evidence_result.v3":
                typed_field = {
                    "trading_status_context": "trading_status_context",
                    "corporate_action_context": "corporate_action_context",
                    "recent_performance": "recent_performance_v3",
                }.get(need)
                if typed_field is not None:
                    is_provided = getattr(evidence_proj, typed_field) is not None
                elif binding is not None and not binding.evidence_artifacts:
                    is_provided = True
            if need in {"material_disclosures", "monthly_revenue"}:
                research_status = _research_status(evidence_proj, need)
                is_provided = research_status in {
                    "available", "partial", "no_evidence_in_covered_scope",
                    "not_yet_available", "not_applicable",
                }
            
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
        for typed_evidence in (evidence_proj.material_disclosures, evidence_proj.monthly_revenue):
            if isinstance(typed_evidence, dict):
                used_cits.update(typed_evidence.get("citation_ids", []))
        for typed_evidence in (
            evidence_proj.trading_status_context,
            evidence_proj.corporate_action_context,
            evidence_proj.recent_performance_v3,
            evidence_proj.discontinuity_safety,
        ):
            if isinstance(typed_evidence, dict):
                typed_ids = typed_evidence.get("citation_ids", [])
                if not isinstance(typed_ids, list) or not set(typed_ids).issubset(citation_index.all_citations):
                    raise ProjectionError("phase_h_citation_lineage_mismatch")
                used_cits.update(typed_ids)
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
        if output_schema_version in {"unified_market_evidence_result.v2", "unified_market_evidence_result.v3"}:
            t_dict["canonical_identity"] = _canonical_identity_v2(res)

        # Evidence fields.
        ev = tp.evidence
        for field_name, env_val in [
            ("identity", ev.identity),
            ("current_observation", ev.current_observation),
            ("recent_performance", ev.recent_performance if output_schema_version != "unified_market_evidence_result.v3" else None),
            ("session_status", ev.session_status),
            ("source_currentness", ev.source_currentness),
            ("evidence_quality", ev.evidence_quality),
        ]:
            d = _envelope_to_dict(env_val)
            if d is not None:
                t_dict["evidence"][field_name] = d

        if ev.official_eod_reference is not None:
            t_dict["evidence"]["official_eod_reference"] = ev.official_eod_reference
        if output_schema_version in {"unified_market_evidence_result.v2", "unified_market_evidence_result.v3"}:
            if ev.material_disclosures is not None:
                t_dict["evidence"]["material_disclosures"] = ev.material_disclosures
            if ev.monthly_revenue is not None:
                t_dict["evidence"]["monthly_revenue"] = ev.monthly_revenue
        if output_schema_version == "unified_market_evidence_result.v3":
            for field_name, typed_evidence in (
                ("trading_status_context", ev.trading_status_context),
                ("corporate_action_context", ev.corporate_action_context),
                ("recent_performance", ev.recent_performance_v3),
                ("discontinuity_safety", ev.discontinuity_safety),
            ):
                if typed_evidence is not None:
                    t_dict["evidence"][field_name] = typed_evidence

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
    if output_schema_version in {"unified_market_evidence_result.v2", "unified_market_evidence_result.v3"}:
        rs_dict["request_schema_version"] = request_summary.request_schema_version or "unified_market_evidence_request.v1"

    # Build body without result_hash.
    body_without_hash: dict = {
        "schema_version": output_schema_version,
        "result_id": result_id,
        "request_id": request_id,
        "generated_at": calculated_at,
        "request_summary": rs_dict,
        "status": result_status,
        "targets": targets_dicts,
        "audit_reference": {
            "audit_package_id": audit_package_id,
            "schema_version": ({
                "unified_market_evidence_result.v1": "unified_market_evidence_audit_package.v1",
                "unified_market_evidence_result.v2": "unified_market_evidence_audit_package.v2",
                "unified_market_evidence_result.v3": "unified_market_evidence_audit_package.v3",
            }[output_schema_version]),
            "relative_path": ({
                "unified_market_evidence_result.v1": AUDIT_PACKAGE_RELATIVE_PATH,
                "unified_market_evidence_result.v2": "audit/unified_market_evidence_audit_package.v2.json",
                "unified_market_evidence_result.v3": "audit/unified_market_evidence_audit_package.v3.json",
            }[output_schema_version]),
        },
    }
    if pf_dicts:
        body_without_hash["partial_failures"] = pf_dicts
    body_without_hash["request_caveats"] = []

    # Compute result_hash.
    result_hash = hash_body_excluding_key(body_without_hash, "result_hash")
    result = {**body_without_hash, "result_hash": result_hash}

    # Validate against schema.
    schema_path = {
        "unified_market_evidence_result.v1": RESULT_SCHEMA_PATH,
        "unified_market_evidence_result.v2": RESULT_V2_SCHEMA_PATH,
        "unified_market_evidence_result.v3": RESULT_V3_SCHEMA_PATH,
    }[output_schema_version]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema).iter_errors(result))
    if errors:
        error_msgs = [str(e.message) for e in errors[:3]]
        raise ProjectionError(f"result_schema_invalid:{'; '.join(error_msgs)}")

    return result
