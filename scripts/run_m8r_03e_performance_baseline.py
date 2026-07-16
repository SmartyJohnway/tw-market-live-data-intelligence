#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import resource as _resource
except ImportError:  # pragma: no cover - exercised by monkeypatch in tests
    _resource = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.m8r_03e_context_validator import (  # noqa: E402
    canonical_json,
    sha256_json,
    validate_watchlist_ai_context_manifest,
    validate_watchlist_ai_context_package,
    validate_watchlist_conversation_handoff,
)
from scripts.m8r_03e_conversation_handoff_builder import (  # noqa: E402
    build_watchlist_conversation_handoff,
)
from scripts.m8r_03e_watchlist_ai_context_builder import (  # noqa: E402
    build_context_manifest,
    build_watchlist_ai_context_package,
)

GENERATOR_VERSION = "m8r_03e_performance_baseline_runner.v1"
BASELINE_SHA = "bd3496efe7492e6cd3c7dacc169e142f90e6cd92"
GENERATED_AT_UTC = "2026-07-16T00:00:00Z"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "m8r_03e"
REQUIRED_SCENARIO_IDS = [
    "1_target_snapshot",
    "10_target_snapshot",
    "50_target_snapshot",
    "100_target_snapshot",
    "high_citation_pressure",
    "high_missing_evidence_pressure",
    "snapshot",
    "performance",
    "partial_failure",
]

SCENARIOS = [
    {
        "scenario_id": "1_target_snapshot",
        "fixture_case": "complete_snapshot",
        "workload_mode": "single_valid_package_truncated_to_first_target",
        "repeat_count": 1,
        "target_limit_per_package": 1,
        "context_policy": None,
    },
    {
        "scenario_id": "10_target_snapshot",
        "fixture_case": "complete_snapshot",
        "workload_mode": "aggregate_valid_packages",
        "repeat_count": 5,
        "target_limit_per_package": None,
        "context_policy": None,
    },
    {
        "scenario_id": "50_target_snapshot",
        "fixture_case": "complete_snapshot",
        "workload_mode": "aggregate_valid_packages",
        "repeat_count": 25,
        "target_limit_per_package": None,
        "context_policy": None,
    },
    {
        "scenario_id": "100_target_snapshot",
        "fixture_case": "complete_snapshot",
        "workload_mode": "aggregate_valid_packages_100_targets_schema_safe",
        "repeat_count": 50,
        "target_limit_per_package": None,
        "context_policy": None,
    },
    {
        "scenario_id": "high_citation_pressure",
        "fixture_case": "context_budget_pressure",
        "workload_mode": "aggregate_valid_packages_high_citation_fixture",
        "repeat_count": 10,
        "target_limit_per_package": None,
        "context_policy": {"max_citations_per_target": 40, "max_serialized_bytes": 250000},
    },
    {
        "scenario_id": "high_missing_evidence_pressure",
        "fixture_case": "all_source_failure",
        "workload_mode": "aggregate_valid_packages_missing_evidence_fixture",
        "repeat_count": 25,
        "target_limit_per_package": None,
        "context_policy": {"max_missing_evidence_entries": 1000, "max_serialized_bytes": 250000},
    },
    {
        "scenario_id": "snapshot",
        "fixture_case": "complete_snapshot",
        "workload_mode": "single_valid_package",
        "repeat_count": 1,
        "target_limit_per_package": None,
        "context_policy": None,
    },
    {
        "scenario_id": "performance",
        "fixture_case": "performance",
        "workload_mode": "single_valid_performance_package",
        "repeat_count": 1,
        "target_limit_per_package": None,
        "context_policy": None,
    },
    {
        "scenario_id": "partial_failure",
        "fixture_case": "partial_source_failure",
        "workload_mode": "single_valid_partial_failure_package",
        "repeat_count": 1,
        "target_limit_per_package": None,
        "context_policy": None,
    },
]



def _peak_memory() -> dict[str, Any]:
    if _resource is None:
        return {"status": "unavailable_on_platform", "value_kb": None, "source": None}
    return {
        "status": "available",
        "value_kb": int(_resource.getrusage(_resource.RUSAGE_SELF).ru_maxrss),
        "source": "resource.getrusage.ru_maxrss",
    }

def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _load_case(case: str) -> dict[str, dict[str, Any]]:
    base = FIXTURE_ROOT / case
    return {
        "validated_request": _load_json(base / "request.json"),
        "execution_plan": _load_json(base / "execution_plan.json"),
        "execution_result": _load_json(base / "execution_result.json"),
        "watchlist_bundle": _load_json(base / "bundle.json"),
    }


def _truncate_to_first_target(upstream: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    data = json.loads(json.dumps(upstream, sort_keys=True))
    target_id = data["validated_request"]["persistent_watchlist_reference"]["enabled_target_ids"][0]
    ids = [target_id]
    data["validated_request"]["persistent_watchlist_reference"]["enabled_target_ids"] = ids
    data["execution_plan"]["target_order"] = ids
    data["execution_plan"]["targets"] = [t for t in data["execution_plan"].get("targets", []) if t.get("target_id") == target_id]
    data["watchlist_bundle"]["targets"] = [t for t in data["watchlist_bundle"].get("targets", []) if t.get("target_id") == target_id]
    data["watchlist_bundle"]["facts"] = [f for f in data["watchlist_bundle"].get("facts", []) if f.get("target_id") == target_id]
    data["watchlist_bundle"].setdefault("coverage", {})["requested_target_ids"] = ids
    data["watchlist_bundle"]["coverage"]["targets"] = [
        t for t in data["watchlist_bundle"].get("coverage", {}).get("targets", []) if t.get("target_id") == target_id
    ]
    data["execution_result"]["target_results"] = [
        t for t in data["execution_result"].get("target_results", []) if t.get("target_id") == target_id
    ]
    data["execution_result"]["observation_count"] = len(data["execution_result"].get("target_results", []))
    for group in data["execution_plan"].get("source_call_groups", []):
        group["target_ids"] = ids
    summary = data["execution_result"].get("source_execution_summary", {})
    for group_key in ("group_results", "planned_source_call_groups"):
        for group in summary.get(group_key, []):
            if group.get("target_ids"):
                group["target_ids"] = ids
    request_hash = sha256_json(data["validated_request"])
    data["execution_plan"]["request_hash"] = request_hash
    data["execution_result"]["request_hash"] = request_hash
    return data


def _exercise_once(
    upstream: dict[str, dict[str, Any]],
    *,
    context_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    build_start = time.perf_counter_ns()
    package = build_watchlist_ai_context_package(
        validated_request=upstream["validated_request"],
        execution_plan=upstream["execution_plan"],
        execution_result=upstream["execution_result"],
        watchlist_bundle=upstream["watchlist_bundle"],
        generated_at_utc=GENERATED_AT_UTC,
        context_policy=context_policy,
    )
    handoff = build_watchlist_conversation_handoff(
        context_package=package,
        generated_at_utc=GENERATED_AT_UTC,
    )
    manifest = build_context_manifest(
        context_package=package,
        conversation_handoff=handoff,
        upstream_artifacts=upstream,
        generated_at_utc=GENERATED_AT_UTC,
    )
    build_end = time.perf_counter_ns()

    validation_start = time.perf_counter_ns()
    package_validation = validate_watchlist_ai_context_package(package, upstream_artifacts=upstream)
    handoff_validation = validate_watchlist_conversation_handoff(handoff, context_package=package)
    manifest_validation = validate_watchlist_ai_context_manifest(
        manifest,
        context_package=package,
        handoff=handoff,
        upstream_artifacts=upstream,
    )
    validation_end = time.perf_counter_ns()

    serialized_bytes = sum(
        len(canonical_json(obj).encode("utf-8")) for obj in (package, handoff, manifest)
    )
    return {
        "build_time_ms": (build_end - build_start) / 1_000_000,
        "validation_time_ms": (validation_end - validation_start) / 1_000_000,
        "serialized_bytes": serialized_bytes,
        "citation_count": len(package.get("citation_index", [])),
        "missing_evidence_count": len(package.get("missing_evidence", [])),
        "target_count": len(package.get("targets", [])),
        "budget_status": package.get("context_budget", {}).get("overall_budget_status"),
        "coverage_status": package.get("coverage_summary", {}).get("coverage_status"),
        "valid": bool(package_validation["valid"] and handoff_validation["valid"] and manifest_validation["valid"]),
        "validation_issue_count": len(package_validation.get("issues", []))
        + len(handoff_validation.get("issues", []))
        + len(manifest_validation.get("issues", [])),
    }


def _round_ms(value: float) -> float:
    return round(value, 3)


def _build_scenario(config: dict[str, Any]) -> dict[str, Any]:
    upstream = _load_case(config["fixture_case"])
    if config.get("target_limit_per_package") == 1:
        upstream = _truncate_to_first_target(upstream)
    totals = {
        "build_time_ms": 0.0,
        "validation_time_ms": 0.0,
        "serialized_bytes": 0,
        "citation_count": 0,
        "missing_evidence_count": 0,
        "target_count": 0,
        "validation_issue_count": 0,
    }
    budget_statuses: list[str | None] = []
    coverage_statuses: list[str | None] = []
    valid = True
    for _ in range(config["repeat_count"]):
        result = _exercise_once(upstream, context_policy=config.get("context_policy"))
        totals["build_time_ms"] += result["build_time_ms"]
        totals["validation_time_ms"] += result["validation_time_ms"]
        for key in ("serialized_bytes", "citation_count", "missing_evidence_count", "target_count", "validation_issue_count"):
            totals[key] += int(result[key])
        budget_statuses.append(result["budget_status"])
        coverage_statuses.append(result["coverage_status"])
        valid = valid and result["valid"]
    return {
        "scenario_id": config["scenario_id"],
        "fixture_case": config["fixture_case"],
        "scenario_construction_method": "repeat checked-in M8R-03E fixture through actual builder/validator/handoff/manifest pipeline",
        "actual_functions_exercised": [
            "build_watchlist_ai_context_package",
            "validate_watchlist_ai_context_package",
            "build_watchlist_conversation_handoff",
            "build_context_manifest",
            "validate_watchlist_conversation_handoff",
            "validate_watchlist_ai_context_manifest",
        ],
        "workload_mode": config["workload_mode"],
        "repeat_count": config["repeat_count"],
        "target_count": totals["target_count"],
        "build_time_ms": _round_ms(totals["build_time_ms"]),
        "validation_time_ms": _round_ms(totals["validation_time_ms"]),
        "serialized_bytes": totals["serialized_bytes"],
        "citation_count": totals["citation_count"],
        "missing_evidence_count": totals["missing_evidence_count"],
        "budget_status": "mixed" if len(set(budget_statuses)) > 1 else budget_statuses[0],
        "coverage_status": "mixed" if len(set(coverage_statuses)) > 1 else coverage_statuses[0],
        "valid": valid,
        "validation_issue_count": totals["validation_issue_count"],
        "context_policy": config.get("context_policy") or {},
    }


def build_baseline() -> dict[str, Any]:
    scenarios = [_build_scenario(config) for config in SCENARIOS]
    one = next(s for s in scenarios if s["scenario_id"] == "1_target_snapshot")
    for scenario in scenarios:
        scenario["growth_ratio_vs_one_target"] = {
            "target_count": round(scenario["target_count"] / max(one["target_count"], 1), 3),
            "build_time": round(scenario["build_time_ms"] / max(one["build_time_ms"], 0.001), 3),
            "validation_time": round(scenario["validation_time_ms"] / max(one["validation_time_ms"], 0.001), 3),
            "serialized_bytes": round(scenario["serialized_bytes"] / max(one["serialized_bytes"], 1), 3),
            "citation_count": round(scenario["citation_count"] / max(one["citation_count"], 1), 3),
            "missing_evidence_count": round(
                scenario["missing_evidence_count"] / max(one["missing_evidence_count"], 1), 3
            ),
        }
    return {
        "schema_version": "m8_performance_baseline.v2",
        "generator_script": "scripts/run_m8r_03e_performance_baseline.py",
        "generator_version": GENERATOR_VERSION,
        "baseline_sha": BASELINE_SHA,
        "repository_head_sha": _sha(),
        "generated_at_utc": GENERATED_AT_UTC,
        "network_execution_used": False,
        "measurement_environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "dependency_free_beyond_repository": True,
            "network": False,
            "timing_source": "time.perf_counter_ns",
            "peak_memory": _peak_memory(),
        },
        "required_scenarios": REQUIRED_SCENARIO_IDS,
        "scenarios": scenarios,
        "summary": {
            "scenario_count": len(scenarios),
            "all_valid": all(s["valid"] for s in scenarios),
            "max_build_time_ms": max(s["build_time_ms"] for s in scenarios),
            "max_validation_time_ms": max(s["validation_time_ms"] for s in scenarios),
            "max_serialized_bytes": max(s["serialized_bytes"] for s in scenarios),
            "max_citation_count": max(s["citation_count"] for s in scenarios),
            "max_missing_evidence_count": max(s["missing_evidence_count"] for s in scenarios),
            "peak_memory": _peak_memory(),
            "production_performance_readiness_claimed": False,
            "observation": "R1 reproducible baseline only; R4 owns optimization and scalability hardening.",
        },
    }


def _scenario_projection(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        scenario["scenario_id"]: {
            "target_count": scenario["target_count"],
            "workload_mode": scenario["workload_mode"],
            "citation_count": scenario["citation_count"],
            "missing_evidence_count": scenario["missing_evidence_count"],
            "valid": scenario["valid"],
            "budget_status": scenario["budget_status"],
            "coverage_status": scenario["coverage_status"],
        }
        for scenario in doc.get("scenarios", [])
    }


def verify_existing(path: Path) -> tuple[bool, list[str]]:
    existing = _load_json(path)
    regenerated = build_baseline()
    issues: list[str] = []
    if existing.get("schema_version") != "m8_performance_baseline.v2":
        issues.append("schema_version_mismatch")
    if existing.get("generator_script") != "scripts/run_m8r_03e_performance_baseline.py":
        issues.append("generator_script_missing_or_mismatch")
    if existing.get("generator_version") != GENERATOR_VERSION:
        issues.append("generator_version_mismatch")
    if existing.get("network_execution_used") is not False:
        issues.append("network_execution_used_must_be_false")
    if existing.get("required_scenarios") != REQUIRED_SCENARIO_IDS:
        issues.append("required_scenarios_mismatch")
    if _scenario_projection(existing) != _scenario_projection(regenerated):
        issues.append("scenario_structural_projection_mismatch")
    return not issues, issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the M8R-03E R1 performance baseline")
    parser.add_argument("--output")
    parser.add_argument("--verify-existing")
    args = parser.parse_args(argv)
    if bool(args.output) == bool(args.verify_existing):
        parser.error("exactly one of --output or --verify-existing is required")
    if args.verify_existing:
        ok, issues = verify_existing(Path(args.verify_existing))
        print(json.dumps({"status": "pass" if ok else "fail", "issues": issues}, sort_keys=True))
        return 0 if ok else 1
    baseline = build_baseline()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "output": str(out), "scenario_count": len(baseline["scenarios"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
