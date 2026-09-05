"""Narrow status aggregation contract for Mode C canonical Results."""
from scripts.m8r_05c.models import (
    PartialFailureProjection,
    ResolutionProjection,
    TargetProjection,
)
from scripts.m8r_05c.evidence_projector import (
    CURRENT_PROJECTOR_VERSION,
    PREVIOUS_PROJECTOR_VERSION,
    OLDER_PROJECTOR_VERSION,
    LEGACY_PROJECTOR_VERSION,
    SUPPORTED_PROJECTOR_VERSIONS,
    _project_official_eod,
    _project_official_eod_pre_v1_3,
)
from scripts.m8r_05c.lineage_resolver import OperationBinding
from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.result_builder import _compute_result_status


def _target(status="resolved", *, provided=None, missing=None):
    return TargetProjection(
        resolution=ResolutionProjection(status=status),
        coverage_provided_needs=provided or [],
        coverage_missing_needs=missing or [],
    )


def _required_failure(target_index=0):
    return PartialFailureProjection(
        target_index=target_index,
        data_need="official_eod_reference",
        reason="required_evidence_missing:official_eod_reference",
        reason_code="required_evidence_missing",
    )


def test_no_targets_is_failed():
    assert _compute_result_status([], []) == "failed"


def test_unresolved_only_is_failed():
    unresolved = _target("not_found")
    failure = PartialFailureProjection(
        target_index=0,
        reason="target_resolution_failed:not_found",
        reason_code="target_resolution_failed",
    )
    assert _compute_result_status([unresolved], [failure]) == "failed"


def test_all_required_evidence_missing_is_failed():
    target = _target(missing=["official_eod_reference"])
    assert _compute_result_status([target], [_required_failure()]) == "failed"


def test_mixed_success_and_required_failure_is_partially_failed():
    provided = _target(provided=["official_eod_reference"])
    missing = _target(missing=["official_eod_reference"])
    assert _compute_result_status([provided, missing], [_required_failure(1)]) == "partially_failed"


def test_optional_coverage_gap_without_failure_is_success_with_partial_coverage():
    target = _target(provided=["current_observation"], missing=["optional_need"])
    assert _compute_result_status([target], []) == "success_with_partial_coverage"


def test_complete_resolved_coverage_is_full_success():
    target = _target(provided=["official_eod_reference"])
    assert _compute_result_status([target], []) == "full_success"


def test_v1_2_preserves_all_required_missing_status_behavior():
    target = _target(missing=["official_eod_reference"])
    assert _compute_result_status(
        [target], [_required_failure()], projector_version=PREVIOUS_PROJECTOR_VERSION
    ) == "partially_failed"
    assert SUPPORTED_PROJECTOR_VERSIONS == frozenset({
        CURRENT_PROJECTOR_VERSION,
        PREVIOUS_PROJECTOR_VERSION,
        OLDER_PROJECTOR_VERSION,
        LEGACY_PROJECTOR_VERSION,
    })


def _failed_eod_binding():
    return OperationBinding(
        "op", "official_eod_reference", "adapter", "TWSE:2330",
        "official_eod_reference", "TWSE", "failed", "official_eod_unavailable",
    )


def test_v1_3_failed_eod_is_explicitly_failed_without_market_values():
    projection = _project_official_eod(_failed_eod_binding(), [])
    assert projection == {
        "status": "failed",
        "currentness_status": "calendar_status_unresolved",
        "caveats": ["operation_failed:official_eod_unavailable"],
    }
    assert "price" not in projection and "activity" not in projection


def test_v1_2_failed_eod_preserves_pre_v1_3_shape():
    projection = _project_official_eod_pre_v1_3(_failed_eod_binding(), [])
    assert projection == {
        "currentness_status": "calendar_status_unresolved",
        "caveats": ["operation_failed:official_eod_unavailable"],
    }


def _failed_result(status="failed"):
    return {
        "status": status,
        "partial_failures": [{
            "target_index": 0,
            "data_need": "official_eod_reference",
            "reason": "required_evidence_missing:official_eod_reference",
        }],
        "targets": [{
            "resolution": {"status": "resolved", "canonical_target_id": "TWSE:2330"},
            "evidence": {"official_eod_reference": _project_official_eod(_failed_eod_binding(), [])},
        }],
    }


def test_v1_3_failed_markdown_uses_failure_status_and_failure_section():
    markdown = render_result_markdown(_failed_result())
    assert "**整體狀態**: ❌ 失敗" in markdown
    assert "## 失敗詳情" in markdown and "## 部分失敗" not in markdown
    assert "**EOD 狀態**: 失敗" in markdown
    assert "operation_failed:official_eod_unavailable" in markdown
    assert "**Price**" not in markdown and "**Activity**" not in markdown


def test_v1_3_partially_failed_markdown_preserves_g5_presentation():
    markdown = render_result_markdown(_failed_result("partially_failed"))
    assert "**整體狀態**: ⚠️ 部分失敗" in markdown
    assert "## 部分失敗" in markdown


def test_v1_2_markdown_preserves_historical_failed_eod_presentation():
    result = _failed_result("partially_failed")
    result["targets"][0]["evidence"]["official_eod_reference"] = (
        _project_official_eod_pre_v1_3(_failed_eod_binding(), [])
    )
    markdown = render_result_markdown(result, projector_version=PREVIOUS_PROJECTOR_VERSION)
    assert "**整體狀態**: ⚠️ 部分失敗" in markdown
    assert "## 部分失敗" in markdown
    assert "**EOD 狀態**: 可用" in markdown


def test_successful_eod_regression_preserves_available_price_and_activity():
    binding = OperationBinding(
        "op", "official_eod_reference", "adapter", "TWSE:2330",
        "official_eod_reference", "TWSE", "succeeded", None,
        artifact_objects={"evidence/op.json": {
            "schema_version": "m8r_06_03_operation_evidence.v1",
            "source_family": "TWSE_OPENAPI",
            "records": [{"symbol": "2330", "market": "listed", "price": {"close": "100"}, "activity": {"trade_volume": 1}}],
        }},
    )
    projection = _project_official_eod(binding, ["citation"])
    assert projection["status"] == "available"
    assert projection["price"] == {"close": "100"}
    assert projection["activity"] == {"trade_volume": 1}
