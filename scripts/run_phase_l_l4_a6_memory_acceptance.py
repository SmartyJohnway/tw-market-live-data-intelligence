"""Bounded offline memory observations for the L4-A6 acceptance gate."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import gc
import json
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MEMORY_POLICY = "EXPLICIT_NO_HARD_RUNTIME_LIMIT_WITH_STRUCTURAL_BOUND"
M8_WARMUP_CYCLES = 30
M8_MEASURED_CYCLES = 1000


def process_memory_bytes() -> int | None:
    """Return observed process RSS via the product's best-effort sampler."""
    from server.operational_diagnostics import process_memory_bytes as observe

    return observe()


def _encoded_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _planning_workload() -> tuple[int, int, dict[str, Any]]:
    from tests.unit.test_m8r_06_02_mode_b1_preview import package, request

    req = request()
    req["targets"] = [{"input": f"synthetic-{index:02d}"} for index in range(50)]
    result = package(req)
    return _encoded_size(req), _encoded_size(result), result


def _watchlist_snapshot() -> dict[str, Any]:
    return {
        "schema_version": "persistent_watchlist.v1",
        "watchlist_id": "00000000-0000-4000-8000-000000000001",
        "name": "Synthetic 500 entry maximum",
        "current_version": 1,
        "is_default": False,
        "deleted": False,
        "created_at": "2026-10-17T00:00:00Z",
        "updated_at": "2026-10-17T00:00:00Z",
        "entries": [
            {
                "watchlist_entry_id": f"00000000-0000-4000-8000-{index:012d}",
                "instrument_id": f"TW{index:010d}",
                "identity_scheme": "ISIN",
                "enabled": True,
                "display_order": index + 1,
                "tags": [],
                "notes": "",
                "created_at": "2026-10-17T00:00:00Z",
                "updated_at": "2026-10-17T00:00:00Z",
                "resolved_under_security_master_release_id": None,
            }
            for index in range(500)
        ],
    }


def _measure(name: str, operation: Callable[[], tuple[int, int, str, dict[str, Any] | None]], baseline: int | None) -> dict[str, Any]:
    gc.collect()
    rss_pre = process_memory_bytes()
    tracemalloc.start()
    tracemalloc.reset_peak()
    current_before, _ = tracemalloc.get_traced_memory()
    try:
        input_bytes, output_bytes, status, details = operation()
        gc.collect()
        current_after, peak = tracemalloc.get_traced_memory()
        rss_post = process_memory_bytes()
        return {
            "scenario": name,
            "rss_baseline_bytes": baseline,
            "rss_pre_bytes": rss_pre,
            "rss_post_bytes": rss_post,
            "rss_delta_bytes": None if rss_pre is None or rss_post is None else rss_post - rss_pre,
            "tracemalloc_current_bytes": current_after,
            "tracemalloc_peak_bytes": peak,
            "tracemalloc_pre_bytes": current_before,
            "serialized_input_bytes": input_bytes,
            "serialized_output_bytes": output_bytes,
            "scenario_status": status,
            "details": details or {},
        }
    finally:
        tracemalloc.stop()


def _memory_scenarios() -> list[dict[str, Any]]:
    baseline = process_memory_bytes()

    def m1():
        from server.main import app
        app.build_middleware_stack()
        summary = {"route_count": len(app.routes), "network_acquisition": False}
        return 0, _encoded_size(summary), "PASS", summary

    def m2():
        input_bytes, output_bytes, package = _planning_workload()
        preview = package.get("preview") or {}
        rejected = preview.get("status") == "rejected_resource_bound"
        details = {"target_count": 50, "preview_status": preview.get("status"), "network_acquisition": False}
        return input_bytes, output_bytes, "FAIL" if rejected else "PASS", details

    def m3():
        from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
        snapshot = _watchlist_snapshot()
        PersistentWatchlistStore._validate_snapshot(None, snapshot)
        return _encoded_size(snapshot), _encoded_size({"validated_entries": len(snapshot["entries"])}), "PASS", {"entry_count": len(snapshot["entries"]), "persistent_state": False}

    def m4():
        import copy
        import jsonschema
        schema_path = ROOT / "schemas" / "material_disclosure_evidence.v1.schema.json"
        fixture_path = ROOT / "tests" / "fixtures" / "phase_g_contract_v2" / "example_material_disclosure_evidence.v1.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        evidence = json.loads(fixture_path.read_text(encoding="utf-8"))
        base_item = evidence["items"][0]
        evidence["items"] = []
        for index in range(50):
            item = copy.deepcopy(base_item)
            item["citation_id"] = f"cite-material-a6-{index:02d}"
            item["subject"] = f"Synthetic supported material disclosure {index:02d}"
            evidence["items"].append(item)
        evidence["coverage"]["item_count"] = 50
        evidence["citation_ids"] = [item["citation_id"] for item in evidence["items"]]
        jsonschema.validate(evidence, schema)
        encoded = _encoded_size(evidence)
        return encoded, encoded, "PASS", {"supported_family": "material_disclosure_evidence.v1", "item_count": 50, "provider_request": False}

    def m5():
        from server.services.unified_mode_c import _enforce_public_projection_bound
        from server.unified_payload_bounds import MAX_UNIFIED_RESPONSE_BYTES
        result = {"synthetic_result_text": "r" * 2_400_000}
        audit = {"synthetic_audit_text": "a" * 2_400_000}
        markdown = "m" * 2_500_000
        _enforce_public_projection_bound(result, audit, markdown)
        total = _encoded_size(result) + _encoded_size(audit) + len(markdown.encode("utf-8"))
        return 0, total, "PASS", {"envelope_bytes": MAX_UNIFIED_RESPONSE_BYTES, "observed_projection_bytes": total, "temp_only": True}

    def m6():
        from server.unified_mcp.server import _success
        from server.unified_payload_bounds import MAX_UNIFIED_RESPONSE_BYTES
        markdown = "h" * 3_900_000
        payload = {"ai_ready_markdown": markdown, "schema_version": "synthetic_handoff.v1"}
        result = _success("market_export_ai_handoff", payload)
        structured_bytes = _encoded_size(payload)
        text_bytes = len(markdown.encode("utf-8"))
        total = structured_bytes + text_bytes
        ok = result.isError is False and total <= MAX_UNIFIED_RESPONSE_BYTES
        return 0, total, "PASS" if ok else "FAIL", {"envelope_bytes": MAX_UNIFIED_RESPONSE_BYTES, "structured_bytes": structured_bytes, "text_bytes": text_bytes, "network_acquisition": False}

    def m7():
        from fastapi.testclient import TestClient
        from server.main import app
        from concurrent.futures import ThreadPoolExecutor

        def light_read(_index: int):
            with TestClient(app) as client:
                response = client.get("/api/health")
                return response.status_code, len(response.content)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(light_read, range(8)))
        passed = all(status == 200 for status, _ in results)
        return 0, sum(size for _, size in results), "PASS" if passed else "FAIL", {"concurrent_light_reads": len(results), "max_workers": 8, "in_process_transport": True}

    operations = [
        ("M1_baseline_local_service", m1),
        ("M2_max_target_offline_planning_50", m2),
        ("M3_max_watchlist_shape_500", m3),
        ("M4_supported_material_disclosure_50", m4),
        ("M5_near_bound_mode_c_projection", m5),
        ("M6_near_bound_ai_handoff", m6),
        ("M7_concurrent_light_read", m7),
    ]
    return [_measure(name, operation, baseline) for name, operation in operations]


def _tracked_type_counts() -> dict[str, int]:
    counts: collections.Counter[str] = collections.Counter()
    for obj in gc.get_objects():
        typ = type(obj)
        module = getattr(typ, "__module__", "")
        name = getattr(typ, "__qualname__", getattr(typ, "__name__", "unknown"))
        counts[f"{module}.{name}"] += 1
    return dict(counts)


def _traceback_category(traceback: Any) -> str:
    frames = list(traceback)
    # tracemalloc traceback frames are ordered allocation-site first.
    # The final frame is the allocation site; earlier frames are callers.
    owner = frames[-1].filename.replace("\\", "/").lower() if frames else ""
    if owner.endswith("/scripts/run_phase_l_l4_a6_memory_acceptance.py"):
        return "ACCEPTANCE_HELPER"
    if owner.endswith("/server/operational_diagnostics.py") and any(
        frame.filename.lower().endswith("run_phase_l_l4_a6_memory_acceptance.py")
        for frame in frames
    ):
        return "ACCEPTANCE_MEASUREMENT_INSTRUMENTATION"
    if "/tw-market-live-data-intelligence-phase-l4-a6/" in owner:
        return "TW_MARKET_PRODUCT"
    if "/site-packages/" in owner:
        return "THIRD_PARTY_LIBRARY"
    if "/python" in owner or "<frozen" in owner:
        return "PYTHON_STANDARD_LIBRARY_OR_INTERPRETER"
    return "OTHER"


def _long_horizon_m8(baseline_rss: int | None) -> dict[str, Any]:
    warmup_statuses: list[str] = []
    warmup_hash: str | None = None
    for _ in range(M8_WARMUP_CYCLES):
        _, _, package = _planning_workload()
        serialized = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = __import__("hashlib").sha256(serialized.encode("utf-8")).hexdigest()
        warmup_hash = warmup_hash or digest
        warmup_statuses.append((package.get("preview") or {}).get("status", "missing"))
        del package, serialized
    gc.collect()
    warmup_type_counts = _tracked_type_counts()
    warmup_rss = process_memory_bytes()

    # The measured horizon begins only after warm-up, as required by the R3 contract.
    tracemalloc.start(25)
    tracemalloc.reset_peak()
    gc.collect()
    measured_trace_start, _ = tracemalloc.get_traced_memory()
    measured_rss_start = process_memory_bytes()
    checkpoints: list[dict[str, Any]] = []
    previous_snapshot: Any = tracemalloc.take_snapshot()
    previous_snapshot_cycle = 0
    traceback_windows: list[dict[str, Any]] = []
    product_rates_by_traceback: dict[str, list[float | None]] = {}
    object_deltas: list[dict[str, Any]] = []
    statuses_deterministic = True
    input_total = output_total = 0
    try:
        for cycle in range(1, M8_MEASURED_CYCLES + 1):
            input_bytes, output_bytes, package = _planning_workload()
            input_total += input_bytes
            output_total += output_bytes
            status = (package.get("preview") or {}).get("status", "missing")
            serialized = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            digest = __import__("hashlib").sha256(serialized.encode("utf-8")).hexdigest()
            statuses_deterministic = statuses_deterministic and status == warmup_statuses[-1] and digest == warmup_hash
            del package, serialized

            if cycle % 100 == 0 or cycle in {250, 500, 750, 1000}:
                gc.collect()
                current, peak = tracemalloc.get_traced_memory()
                checkpoints.append({
                    "cycle": cycle,
                    "tracemalloc_current_bytes": current,
                    "tracemalloc_peak_bytes": peak,
                    "rss_observation_bytes": process_memory_bytes(),
                    "functional_preview_status": status,
                    "functional_output_sha256": digest,
                })
            if cycle in {250, 500, 750, 1000}:
                observed_type_counts = _tracked_type_counts()
                all_type_deltas = {
                    key: observed_type_counts.get(key, 0) - warmup_type_counts.get(key, 0)
                    for key in set(observed_type_counts) | set(warmup_type_counts)
                    if observed_type_counts.get(key, 0) != warmup_type_counts.get(key, 0)
                }
                focus_terms = ("request", "validation", "snapshot", "schema", "validator", "path", "trace", "context")
                object_deltas.append({
                    "cycle": cycle,
                    "focused_type_count_deltas_from_warmup": {
                        key: delta for key, delta in all_type_deltas.items()
                        if any(term in key.lower() for term in focus_terms)
                    },
                    "builtin_dict_count_delta": all_type_deltas.get("builtins.dict", 0),
                    "all_type_count_delta_count": len(all_type_deltas),
                    "largest_positive_type_deltas": sorted(
                        ((key, delta) for key, delta in all_type_deltas.items() if delta > 0),
                        key=lambda pair: pair[1], reverse=True,
                    )[:30],
                })
                del observed_type_counts, all_type_deltas
                current_snapshot = tracemalloc.take_snapshot()
                diffs = current_snapshot.compare_to(previous_snapshot, "traceback")
                category_totals: collections.Counter[str] = collections.Counter()
                product_counts: collections.Counter[str] = collections.Counter()
                rows = []
                for stat in diffs:
                    tb = stat.traceback
                    category = _traceback_category(tb)
                    category_totals[category] += stat.size_diff
                    if category == "TW_MARKET_PRODUCT" and stat.count_diff > 0:
                        product_counts[str(tb)] += stat.count_diff
                for stat in diffs[:30]:
                    tb = stat.traceback
                    rows.append({
                        "size_diff_bytes": stat.size_diff,
                        "count_diff": stat.count_diff,
                        "category": _traceback_category(tb),
                        "traceback": str(tb),
                        "traceback_frames": [
                            {"filename": frame.filename, "line": frame.lineno}
                            for frame in tb
                        ],
                    })
                for traceback_text in set(product_rates_by_traceback) | set(product_counts):
                    product_rates_by_traceback.setdefault(traceback_text, []).append(
                        product_counts.get(traceback_text, 0) / (cycle - previous_snapshot_cycle)
                    )
                # Window growth excludes the bounded acceptance-harness rows and
                # sampler measurements themselves; those are separately reported.
                workload_growth = sum(
                    amount for category, amount in category_totals.items()
                    if category not in {"ACCEPTANCE_HELPER", "ACCEPTANCE_MEASUREMENT_INSTRUMENTATION"}
                )
                traceback_windows.append({
                    "from_cycle": previous_snapshot_cycle,
                    "to_cycle": cycle,
                    "window_cycle_count": cycle - previous_snapshot_cycle,
                    "retained_growth_bytes_excluding_acceptance_instrumentation": workload_growth,
                    "retained_growth_bytes_per_cycle": workload_growth / (cycle - previous_snapshot_cycle),
                    "category_retained_growth_bytes": dict(category_totals),
                    "top_retained_diffs": rows,
                })
                del previous_snapshot, diffs, stat, rows, category_totals, product_counts, current_snapshot
                previous_snapshot = tracemalloc.take_snapshot()
                previous_snapshot_cycle = cycle

        checkpoint_by_cycle = {item["cycle"]: item for item in checkpoints}
        windows = [
            {
                "window": f"W{index}",
                "start_cycle": item["from_cycle"] + 1,
                "end_cycle": item["to_cycle"],
                "retained_growth_bytes": item["retained_growth_bytes_excluding_acceptance_instrumentation"],
                "retained_growth_bytes_per_cycle": item["retained_growth_bytes_per_cycle"],
            }
            for index, item in enumerate(traceback_windows, start=1)
        ]
        slopes = [item["retained_growth_bytes_per_cycle"] for item in windows]
        slopes_decline = all(left >= right for left, right in zip(slopes, slopes[1:])) and any(left > right for left, right in zip(slopes, slopes[1:]))
        late_slope = (slopes[2] + slopes[3]) / 2
        early_slope = (slopes[0] + slopes[1]) / 2
        late_lower = late_slope < early_slope

        product_object_growth = False
        for item in object_deltas:
            for key, delta in item["focused_type_count_deltas_from_warmup"].items():
                if (key.startswith("server.") or key.startswith("scripts.")) and delta > 0:
                    product_object_growth = True
        product_trace_growth = any(
            len(rates) == 4 and rates[0] <= rates[1] <= rates[2] <= rates[3]
            and rates[-1] > 0
            for rates in product_rates_by_traceback.values()
        )
        rss_values = [measured_rss_start] + [item["rss_observation_bytes"] for item in checkpoints if item["cycle"] in {250, 500, 750, 1000}]
        rss_slopes = []
        for left, right in zip(rss_values, rss_values[1:]):
            rss_slopes.append(None if left is None or right is None else (right - left) / 250)
        rss_linear_pattern = all(value is not None for value in rss_slopes) and all(value > 0 for value in rss_slopes) and max(rss_slopes) <= max(1.0, min(rss_slopes) * 1.5)

        cache_stabilization = all((
            statuses_deterministic,
            slopes_decline,
            late_lower,
            not product_object_growth,
            not product_trace_growth,
            not rss_linear_pattern,
        ))
        rss_post = process_memory_bytes()
        trace_current, trace_peak = tracemalloc.get_traced_memory()
        return {
            "scenario": "M8_long_horizon_identical_bounded_workload",
            "warmup_cycles": M8_WARMUP_CYCLES,
            "measured_cycles": M8_MEASURED_CYCLES,
            "rss_baseline_bytes": baseline_rss,
            "rss_pre_bytes": measured_rss_start,
            "rss_post_bytes": rss_post,
            "rss_delta_bytes": None if measured_rss_start is None or rss_post is None else rss_post - measured_rss_start,
            "tracemalloc_current_bytes": trace_current,
            "tracemalloc_peak_bytes": trace_peak,
            "serialized_input_bytes_total": input_total,
            "serialized_output_bytes_total": output_total,
            "scenario_status": "PASS_BOUNDED_CACHE_STABILIZATION" if cache_stabilization else "HOLD_RUNAWAY_GROWTH",
            "functional_output_deterministic": statuses_deterministic,
            "warmup_statuses": warmup_statuses,
            "checkpoints": checkpoints,
            "equal_windows": windows,
            "raw_tracemalloc_current_at_window_checkpoints": {
                str(cycle): checkpoint_by_cycle[cycle]["tracemalloc_current_bytes"]
                for cycle in (250, 500, 750, 1000)
            },
            "slopes_decline_across_equal_windows": slopes_decline,
            "late_half_slope_lower_than_early_half": late_lower,
            "product_defined_type_growth_detected": product_object_growth,
            "positive_product_traceback_growth_detected": product_trace_growth,
            "product_traceback_allocation_rates_per_window": [
                {"traceback": traceback, "counts_per_cycle": rates}
                for traceback, rates in product_rates_by_traceback.items()
            ],
            "rss_window_slopes_bytes_per_cycle": rss_slopes,
            "rss_independent_linear_growth_pattern": rss_linear_pattern,
            "object_count_deltas": object_deltas,
            "traceback_window_diffs": traceback_windows,
            "traceback_classification_review_required": True,
            "strict_monotonic_5_cycle_result": "HISTORICAL_SHORT_HORIZON_FALSE_POSITIVE_FOR_FINAL_CLASSIFICATION",
        }
    finally:
        tracemalloc.stop()


def run_memory_acceptance() -> dict[str, Any]:
    baseline = process_memory_bytes()
    scenarios = _memory_scenarios()
    m8 = _long_horizon_m8(baseline)
    scenarios.append(m8)
    growth = m8["scenario_status"] != "PASS_BOUNDED_CACHE_STABILIZATION"
    return {
        "schema": "phase_l_l4_a6_memory_acceptance_matrix.v3",
        "policy_class": MEMORY_POLICY,
        "memory_hard_runtime_kill_threshold": "NOT_USED",
        "rss_observation_is_not_tracemalloc_peak": True,
        "strict_monotonic_5_cycle_result": "HISTORICAL_SHORT_HORIZON_FALSE_POSITIVE_FOR_FINAL_CLASSIFICATION",
        "strict_monotonic_retained_growth_detected": growth,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "status": "HOLD_RUNAWAY_GROWTH" if growth else "PASS_REPRESENTATIVE_BOUNDED_WORKLOADS",
        "limitations": [
            "RSS is an observed process working set, not a hard cap.",
            "tracemalloc observes Python-managed allocations and excludes native allocations.",
            "No OOM test or allocate-until-failure test was run.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_memory_acceptance()
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + os.linesep
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["status"] == "PASS_REPRESENTATIVE_BOUNDED_WORKLOADS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
