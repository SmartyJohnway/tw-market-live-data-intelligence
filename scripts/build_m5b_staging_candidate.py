from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ALLOWED = {"2330", "0050", "00929"}
SUCCESS_CONTRACT_STATUSES = {"normalized_pass", "partial_pass"}
ARTIFACT_TYPES = {
    "authorization_snapshot.json": "authorization_snapshot",
    "request_snapshot.json": "request_snapshot",
    "execution_receipt.json": "execution_receipt",
    "bounded_probe_result.json": "bounded_probe_result",
    "bounded_normalized_rows.json": "bounded_normalized_rows",
    "source_contract_assessment.json": "source_contract_assessment",
    "freshness_delay_assessment.json": "freshness_delay_assessment",
    "run_summary.json": "run_summary",
    "staging_candidate.json": "staging_candidate",
}
RUNNER_PRODUCED = {
    "authorization_snapshot.json",
    "request_snapshot.json",
    "execution_receipt.json",
    "bounded_probe_result.json",
    "bounded_normalized_rows.json",
    "source_contract_assessment.json",
    "freshness_delay_assessment.json",
    "run_summary.json",
}


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _existing_final_manifest(run_path: Path) -> bool:
    manifest_path = run_path / "sha256_manifest.json"
    if not manifest_path.exists():
        return False
    try:
        return _load(manifest_path).get("manifest_final") is True
    except Exception:
        return False


def _artifact_entry(run_dir: Path, file_name: str) -> dict:
    produced_by = "scripts/run_m5b_controlled_live_probe.py" if file_name in RUNNER_PRODUCED else "scripts/build_m5b_staging_candidate.py"
    return {
        "artifact_path": str(run_dir / file_name),
        "artifact_type": ARTIFACT_TYPES.get(file_name, "m5b_artifact"),
        "sha256": _sha256(run_dir / file_name),
        "lineage": {
            "run_id": run_dir.name,
            "source_id": "TWSE_OpenAPI",
            "derived_from": "bounded M5B controlled live-probe evidence",
        },
        "produced_by": produced_by,
        "cataloged_by": "scripts/build_m5b_staging_candidate.py",
        "promotion_status": {
            "staging_only": True,
            "production_promoted": False,
            "frontend_published": False,
            "generated_artifact_promoted": False,
            "trading_signal": False,
        },
    }


def _assert_no_forbidden_payload(obj: object, path: str = "$", errors: list[dict] | None = None) -> list[dict]:
    errors = [] if errors is None else errors
    forbidden_keys = {"raw_full_response", "full_raw_payload", "buy", "sell", "hold", "target_price", "recommendation"}
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in forbidden_keys:
                errors.append({"code": "forbidden_field", "path": child})
            if key == "realtime_guaranteed" and value is not False:
                errors.append({"code": "forbidden_realtime_guarantee", "path": child})
            _assert_no_forbidden_payload(value, child, errors)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            _assert_no_forbidden_payload(value, f"{path}[{idx}]", errors)
    return errors


def _validate_rows_for_candidate(result: dict) -> list[dict]:
    rows = result.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("bounded result rows must be a list")
    symbols = [str(row.get("symbol", "")) for row in rows if isinstance(row, dict)]
    unauthorized = sorted(set(symbols) - ALLOWED)
    if unauthorized:
        raise ValueError(f"unauthorized symbol in bounded result: {unauthorized}")
    if len(symbols) != len(set(symbols)):
        raise ValueError("duplicate symbol in bounded result")
    forbidden = _assert_no_forbidden_payload(result)
    if forbidden:
        raise ValueError(f"forbidden bounded result fields: {forbidden}")
    return rows


def _base_from_result(result: dict) -> dict:
    return {k: result.get(k) for k in [
        "run_id", "source_id", "requested_targets", "retained_targets", "retrieved_at_utc", "source_timestamp",
        "http_status", "contract_status", "parse_status", "normalization_status", "failed_targets", "errors",
        "caveats", "production_current_state", "realtime_guaranteed", "trading_signal",
        "generated_artifact_promoted", "frontend_published",
    ]}


def finalize(run_dir: str | Path, *, create_candidate: bool, allow_refinalize: bool = False) -> dict:
    run_path = Path(run_dir)
    if _existing_final_manifest(run_path) and not allow_refinalize:
        raise ValueError("final manifest already exists; refusing to re-finalize without explicit override")
    result = _load(run_path / "bounded_probe_result.json")
    contract_status = result.get("contract_status")
    if create_candidate and contract_status not in SUCCESS_CONTRACT_STATUSES:
        raise ValueError(f"staging candidate requires successful contract status, got {contract_status}")

    candidate = None
    if create_candidate:
        rows = _validate_rows_for_candidate(result)
        candidate = {k: result.get(k) for k in [
            "run_id", "source_id", "requested_targets", "retained_targets", "retrieved_at_utc",
            "source_timestamp", "http_status", "contract_status", "parse_status", "normalization_status",
            "failed_targets", "errors", "caveats", "production_current_state", "realtime_guaranteed",
            "trading_signal", "generated_artifact_promoted", "frontend_published",
        ]}
        candidate.update({
            "rows": rows,
            "staging_only": True,
            "production_ready": False,
            "promotion_authorized": False,
            "frontend_publication_authorized": False,
            "generated_artifact_write": False,
        })
        _write_json(run_path / "staging_candidate.json", candidate)
    elif (run_path / "staging_candidate.json").exists():
        raise ValueError("failure finalization must not retain staging_candidate.json")

    summary = _load(run_path / "run_summary.json")
    summary["staging_candidate_created"] = bool(create_candidate)
    _write_json(run_path / "run_summary.json", summary)

    base = _base_from_result(result)
    ledger_files = [name for name in ARTIFACT_TYPES if name != "evidence_ledger.json" and (run_path / name).exists()]
    ledger = {
        **base,
        "finalized_at_utc": str(base.get("retrieved_at_utc")),
        "artifacts": [_artifact_entry(run_path, name) for name in sorted(ledger_files)],
    }
    _write_json(run_path / "evidence_ledger.json", ledger)

    manifest_files = sorted(p for p in run_path.glob("*.json") if p.name != "sha256_manifest.json")
    manifest = {
        **base,
        "finalized_at_utc": ledger["finalized_at_utc"],
        "manifest": {p.name: _sha256(p) for p in manifest_files},
        "manifest_status": "pass",
        "manifest_final": True,
        "no_artifact_modification_after_manifest": True,
    }
    _write_json(run_path / "sha256_manifest.json", manifest)
    return candidate or {"staging_only": False, "retained_targets": result.get("retained_targets", [])}


def build(run_dir: str | Path, *, allow_refinalize: bool = False) -> dict:
    return finalize(run_dir, create_candidate=True, allow_refinalize=allow_refinalize)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--allow-refinalize", action="store_true", help="Explicitly replace an existing final manifest; default refuses immutable finalization")
    args = ap.parse_args(argv)
    try:
        candidate = build(args.run_dir, allow_refinalize=args.allow_refinalize)
        print(json.dumps({
            "ok": True,
            "path": str(Path(args.run_dir) / "staging_candidate.json"),
            "retained_targets": candidate["retained_targets"],
            "staging_only": True,
            "manifest_finalized": True,
        }, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
