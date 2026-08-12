"""Deterministic derived metric calculations for M8R-05C.

All functions are pure:
- Inputs must be supplied explicitly (no I/O).
- calculated_at must be provided by caller (no datetime.now()).
- Missing inputs → explicit unavailable status.
- Invalid inputs (zero division, bad dates) → explicit invalid status.
- No network calls.
- No investment recommendations.
"""
from __future__ import annotations

from .models import DerivedMetricProjection

_CALCULATION_VERSION = "m8r_05c_v1"


def _safe_pct_change(current: float | None, previous: float | None) -> float | None:
    """Compute (current - previous) / |previous| * 100, or None if invalid."""
    if current is None or previous is None:
        return None
    if previous == 0:
        return None  # invalid denominator
    return (current - previous) / abs(previous) * 100.0


def project_recent_performance_metrics(
    *,
    canonical_target_id: str,
    recent_performance_artifact: dict | None,
    calculated_at: str,
    citation_ids: list[str],
    lookback_trading_days: int | None = None,
    plan_only_not_executed: bool = False,
) -> list[DerivedMetricProjection]:
    """Project derived metrics from a recent_performance evidence artifact.

    Returns an empty list if the data_need was not requested.
    Returns metrics with status=unavailable if artifact is absent.
    Returns metrics with status=invalid if values are not computable.
    """
    if recent_performance_artifact is None:
        return [
            DerivedMetricProjection(
                metric_id="recent_return_pct",
                metric_name="Recent Return (%)",
                status="unavailable",
                invalid_reason=("recent_performance_plan_only_not_executed" if plan_only_not_executed else "no_recent_performance_artifact"),
                calculated_at=calculated_at,
                calculation_version=_CALCULATION_VERSION,
            )
        ]

    # Try to extract period_return_pct if already pre-computed by executor.
    items = recent_performance_artifact.get("items", [recent_performance_artifact])
    if not isinstance(items, list):
        items = [recent_performance_artifact]

    metrics: list[DerivedMetricProjection] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        # Use pre-computed return if available.
        period_return_pct = item.get("period_return_pct")
        if period_return_pct is not None:
            try:
                value = float(period_return_pct)
                window_desc = (
                    f"{lookback_trading_days}td" if lookback_trading_days else "unknown_window"
                )
                metrics.append(
                    DerivedMetricProjection(
                        metric_id="recent_return_pct",
                        metric_name="Recent Return (%)",
                        status="available",
                        value=round(value, 4),
                        unit="percent",
                        method="direct_from_evidence",
                        formula_or_definition="period_return_pct from executor evidence artifact",
                        window=window_desc,
                        input_evidence_references=[canonical_target_id + "::recent_performance"],
                        calculation_version=_CALCULATION_VERSION,
                        calculated_at=calculated_at,
                        citation_ids=citation_ids,
                    )
                )
                break
            except (TypeError, ValueError):
                pass

        # Fallback: compute from close_start and close_end if available.
        close_start = item.get("close_start") or item.get("period_start_close")
        close_end = item.get("close_end") or item.get("period_end_close")
        if close_start is not None and close_end is not None:
            try:
                c_start = float(close_start)
                c_end = float(close_end)
                pct = _safe_pct_change(c_end, c_start)
                if pct is not None:
                    window_desc = (
                        f"{lookback_trading_days}td" if lookback_trading_days else "unknown_window"
                    )
                    metrics.append(
                        DerivedMetricProjection(
                            metric_id="recent_return_pct",
                            metric_name="Recent Return (%)",
                            status="available",
                            value=round(pct, 4),
                            unit="percent",
                            method="computed",
                            formula_or_definition="(close_end - close_start) / |close_start| * 100",
                            window=window_desc,
                            input_evidence_references=[
                                canonical_target_id + "::recent_performance"
                            ],
                            calculation_version=_CALCULATION_VERSION,
                            calculated_at=calculated_at,
                            citation_ids=citation_ids,
                        )
                    )
                else:
                    metrics.append(
                        DerivedMetricProjection(
                            metric_id="recent_return_pct",
                            metric_name="Recent Return (%)",
                            status="invalid",
                            invalid_reason="zero_or_null_start_price",
                            calculation_version=_CALCULATION_VERSION,
                            calculated_at=calculated_at,
                        )
                    )
                break
            except (TypeError, ValueError):
                pass

    if not metrics:
        metrics.append(
            DerivedMetricProjection(
                metric_id="recent_return_pct",
                metric_name="Recent Return (%)",
                status="unavailable",
                invalid_reason="required_fields_absent_in_artifact",
                calculation_version=_CALCULATION_VERSION,
                calculated_at=calculated_at,
            )
        )

    return metrics


def project_derived_metrics(
    *,
    canonical_target_id: str,
    requested_data_needs: list[str],
    target_bindings: dict,
    calculated_at: str,
    citation_map: dict[str, list[str]],
    request_parameters: dict[str, dict] | None = None,
    enable_plan_only_reason: bool = True,
) -> list[DerivedMetricProjection]:
    """Project all applicable derived metrics for one canonical target.

    Parameters
    ----------
    canonical_target_id:
        The resolved target.
    requested_data_needs:
        All requested data_need types from the request.
    target_bindings:
        data_need → OperationBinding mapping for this target.
    calculated_at:
        ISO-8601 UTC string from CLI.
    citation_map:
        key = f"{canonical_target_id}::{data_need}"  →  list[citation_id].
    request_parameters:
        data_need_type → parameters dict from request (for recent_performance).
    """
    if request_parameters is None:
        request_parameters = {}

    metrics: list[DerivedMetricProjection] = []

    if "recent_performance" in requested_data_needs:
        binding = target_bindings.get("recent_performance")
        artifact_obj: dict | None = None
        if binding and binding.status == "succeeded" and binding.artifact_objects:
            # Use the first available artifact.
            artifact_obj = next(iter(binding.artifact_objects.values()), None)

        lookback = None
        rp_params = request_parameters.get("recent_performance", {})
        if isinstance(rp_params, dict):
            lookback = rp_params.get("lookback_trading_days")

        cite_ids = citation_map.get(f"{canonical_target_id}::recent_performance", [])
        metrics.extend(
            project_recent_performance_metrics(
                canonical_target_id=canonical_target_id,
                recent_performance_artifact=artifact_obj,
                calculated_at=calculated_at,
                citation_ids=cite_ids,
                lookback_trading_days=lookback,
                plan_only_not_executed=bool(enable_plan_only_reason and binding and binding.status == "plan_only_not_executed"),
            )
        )

    return metrics
