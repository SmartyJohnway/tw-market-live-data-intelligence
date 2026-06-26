"""Fixture replay simulator for controlled-refresh staging payload scenarios."""
from __future__ import annotations
import argparse, json, sys
from copy import deepcopy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload
from scripts.build_frontend_readonly_context_package import build_frontend_readonly_context_package
from scripts.forbidden_behavior_scanner import scan_text


def _load_scenario_payload(scenario: dict):
    if "payload" in scenario:
        return deepcopy(scenario["payload"])
    fixture = Path(scenario["input_fixture"])
    data = json.loads(fixture.read_text(encoding="utf-8"))
    if isinstance(data, list):
        name = scenario.get("invalid_payload_name")
        if name:
            for row in data:
                if row.get("name") == name:
                    return deepcopy(row.get("payload"))
        return deepcopy(data[0].get("payload", data[0]))
    return data


def _scenario_forbidden_findings(scenario: dict, payload) -> list[dict]:
    if scenario.get("forbidden_behaviors_absent") is False:
        return scan_text(json.dumps(payload, sort_keys=True), scenario.get("scenario_id", "scenario"))
    findings = scan_text(json.dumps(payload, sort_keys=True), scenario.get("scenario_id", "scenario"))
    return findings


def _expected_flags_satisfied(expected: list[str], validation_errors: list[dict], forbidden_findings: list[dict]) -> bool:
    if not expected:
        return not forbidden_findings
    observed = {e.get("code") for e in validation_errors} | {f.get("code") for f in forbidden_findings}
    observed_text = json.dumps({"validation_errors": validation_errors, "forbidden_findings": forbidden_findings}, sort_keys=True)
    def satisfied(flag: str) -> bool:
        return (
            flag in observed
            or any(flag in code for code in observed if code)
            or (flag == "realtime_guarantee" and "realtime_guaranteed" in observed_text)
            or (flag == "trading_signal" and any(term in observed_text for term in ["buy", "sell", "hold", "target_price", "recommendation", "rank"]))
        )
    return all(satisfied(flag) for flag in expected)


def run_scenarios(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    results, events = [], []
    for scenario in data.get("scenarios", []):
        scenario_id = scenario["scenario_id"]
        events.append({"event_type": "scenario_loaded", "scenario_id": scenario_id})
        payload = _load_scenario_payload(scenario)
        validation_errors = validate_controlled_refresh_staging_payload(payload)
        validation_status = "valid" if not validation_errors else "invalid"
        events.append({"event_type": "staging_validated" if not validation_errors else "staging_rejected", "scenario_id": scenario_id})
        package = None
        package_caveats = []
        if not validation_errors:
            package = build_frontend_readonly_context_package(payload)
            package_caveats = sorted(set(package.get("global_caveats", [])) | {c for row in package.get("symbols", []) for c in row.get("display_caveats", [])})
            events.append({"event_type": "frontend_package_built", "scenario_id": scenario_id})
            for caveat in package_caveats:
                events.append({"event_type": "caveat_emitted", "scenario_id": scenario_id, "caveat": caveat})
        forbidden_findings = _scenario_forbidden_findings(scenario, payload)
        for finding in forbidden_findings:
            events.append({"event_type": "forbidden_behavior_detected", "scenario_id": scenario_id, "code": finding["code"]})
        expected_caveats = set(scenario.get("expected_frontend_caveats", []))
        forbidden_behavior_present = bool(forbidden_findings) or any(error.get("code") == "forbidden_field" for error in validation_errors)
        checks = {
            "validation_status": validation_status == scenario.get("expected_validation_status"),
            "frontend_caveats": expected_caveats.issubset(set(package_caveats)),
            "forbidden_flags": _expected_flags_satisfied(scenario.get("expected_forbidden_flags", []), validation_errors, forbidden_findings),
            "forbidden_behaviors_absent": (not forbidden_behavior_present) == bool(scenario.get("forbidden_behaviors_absent", True)),
        }
        actual_summary_status = "pass" if all(checks.values()) else "fail"
        checks["summary_status"] = actual_summary_status == scenario.get("expected_summary_status", "pass")
        passed = all(checks.values())
        results.append({
            "scenario_id": scenario_id,
            "validation_status": validation_status,
            "expected_validation_status": scenario.get("expected_validation_status"),
            "frontend_caveats": package_caveats,
            "expected_frontend_caveats": sorted(expected_caveats),
            "forbidden_findings": forbidden_findings,
            "validation_errors": validation_errors,
            "actual_summary_status": actual_summary_status,
            "expected_summary_status": scenario.get("expected_summary_status", "pass"),
            "checks": checks,
            "passed": passed,
        })
    events.append({"event_type": "summary_completed"})
    failed = sum(not r["passed"] for r in results)
    return {
        "total_scenarios": len(results),
        "passed": len(results) - failed,
        "failed": failed,
        "results": results,
        "audit_events": events,
        "production_current_state_claim": False,
        "summary_status": "pass" if failed == 0 else "fail",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", default="tests/fixtures/replay_scenarios/valid_replay_scenarios.json")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--write-output")
    args = ap.parse_args(argv)
    result = run_scenarios(args.scenarios)
    if args.write_output:
        from scripts.build_fixture_hash_manifest import is_forbidden_output_path
        if is_forbidden_output_path(args.write_output):
            raise SystemExit("forbidden output path")
        Path(args.write_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
