"""S3-R1 bounded merge verdict and non-mutating pytest observation plugin.

No failure is filtered from pytest. This plugin only records selection/outcomes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FLOOR = "config/current_test_coverage_floor.v1.json"
_selected = []
_reports = {}


def pytest_collection_finish(session):
    _selected[:] = [item.nodeid for item in session.items]


def pytest_runtest_logreport(report):
    _reports.setdefault(report.nodeid, []).append({
        "when": report.when, "outcome": report.outcome,
        "wasxfail": hasattr(report, "wasxfail"),
        "detail": str(report.longrepr) if report.skipped else "",
    })


def pytest_sessionfinish(session, exitstatus):
    target = os.environ.get("TWMARKET_S3_OBSERVATION")
    if target:
        Path(target).write_text(json.dumps({"selected": _selected, "reports": _reports,
                                           "exitstatus": int(exitstatus)}), encoding="utf-8")


def observe(profile, *, collect=False, quiet=False, root=ROOT):
    with tempfile.TemporaryDirectory(prefix="twmarket-s3-") as directory:
        target = Path(directory) / "observation.json"
        env = dict(os.environ, TWMARKET_S3_OBSERVATION=str(target), PYTHONDONTWRITEBYTECODE="1")
        # Do not inherit caller-supplied pytest selection overrides.
        env.pop("PYTEST_ADDOPTS", None)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        command = [sys.executable, "-B", "-m", "pytest", "-o", "addopts=",
                   "-p", "scripts.run_current_merge_gate", "-m", profile["pytest_expression"],
                   *profile["pytest_paths"]]
        if collect:
            command += ["--collect-only", "-q"]
        proc = subprocess.run(command, cwd=root, env=env, timeout=3600,
                              stdout=subprocess.PIPE if quiet else None,
                              stderr=subprocess.STDOUT if quiet else None, text=True)
        if not target.is_file():
            raise ValueError("pytest observation missing")
        result = json.loads(target.read_text(encoding="utf-8"))
        if result["exitstatus"] != proc.returncode:
            raise ValueError("pytest exit status mismatch")
        if collect and proc.returncode != 0:
            raise ValueError("collection failed: " + str(proc.stdout)[-3000:])
        return result


def check_selection(floor, name, selected):
    missing = set(floor["profiles"][name]["selected_nodes"]) - set(selected)
    if missing:
        raise ValueError(f"governed selection disappeared: {name}: {sorted(missing)}")


def classify(floor, observation):
    selected = set(observation["selected"])
    known = floor["known_diagnostics"]
    required = set(floor["profiles"]["default-ci"]["selected_nodes"]) | set(known)
    blocking = []
    diagnostics = []
    now_passing = []
    missing = sorted(required - selected)
    for node in sorted(selected):
        reports = observation["reports"].get(node, [])
        skipped = [r for r in reports if r["outcome"] == "skipped"]
        allowed = floor["authorized_optional_skips"].get(node)
        authorized_skip = (allowed and node not in known and len(skipped) == 1
                           and allowed in skipped[0]["detail"])
        invalid = (not reports or any(r["wasxfail"] for r in reports)
                   or (bool(skipped) and not authorized_skip)
                   or (not authorized_skip and any(
                       not any(r["when"] == phase and r["outcome"] == "passed" for r in reports)
                       for phase in ("setup", "teardown")))
                   or any(r["outcome"] == "failed" and r["when"] != "call" for r in reports))
        failed = any(r["outcome"] == "failed" for r in reports)
        completed = any(r["when"] == "call" and r["outcome"] == "passed" for r in reports)
        if invalid or (not failed and not completed and not authorized_skip):
            blocking.append({"nodeid": node, "classification": "BLOCKING_CURRENT_FAILURE", "reason": "unexpected non-pass/incomplete"})
        elif failed:
            if node in known:
                diagnostics.append({"nodeid": node, "classification": known[node]})
            else:
                blocking.append({"nodeid": node, "classification": "BLOCKING_CURRENT_FAILURE", "reason": "unexpected failure"})
        elif node in known:
            now_passing.append(node)
    observed_failure = any(r["outcome"] == "failed" for rs in observation["reports"].values() for r in rs)
    valid_exit = observation["exitstatus"] == (1 if observed_failure else 0)
    verdict = "PASS" if not blocking and not missing and valid_exit else "FAIL"
    return {"schema_version": "current_merge_verdict.v1", "MERGE_VERDICT": verdict, "blocking_failures": len(blocking),
            "blocking_details": blocking, "known_diagnostic_failures": len(diagnostics),
            "known_diagnostics": diagnostics, "known_diagnostic_now_passing": now_passing,
            "missing_required_nodes": missing, "coverage_status": "FAIL" if missing else "PASS",
            "raw_pytest_exitstatus": observation["exitstatus"], "selected_nodes": sorted(selected)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from scripts.validate_current_test_governance import validate, load
    try:
        validation = validate()
        floor = load(ROOT / FLOOR)
        profile = load(ROOT / "config/test_execution_profiles.json")["profiles"]["default-ci"]
        result = classify(floor, observe(profile))
        result["governance"] = validation
    except (ValueError, subprocess.TimeoutExpired) as exc:
        result = {"MERGE_VERDICT": "FAIL", "governance_error": str(exc)}
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["MERGE_VERDICT"] == "PASS" else 1


if __name__ == "__main__":
    # Direct script invocation must expose repository package imports.
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
