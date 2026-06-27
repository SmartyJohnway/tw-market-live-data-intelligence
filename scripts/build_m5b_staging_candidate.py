from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ALLOWED = {"2330", "0050", "00929"}
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


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _artifact_entry(run_dir: Path, file_name: str, produced_by: str) -> dict:
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


def build(run_dir: str | Path) -> dict:
    run_path = Path(run_dir)
    result = _load(run_path / "bounded_probe_result.json")
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

    summary = _load(run_path / "run_summary.json")
    summary["staging_candidate_created"] = True
    _write_json(run_path / "run_summary.json", summary)

    base = {k: result.get(k) for k in [
        "run_id", "source_id", "requested_targets", "retained_targets", "retrieved_at_utc", "source_timestamp",
        "http_status", "contract_status", "parse_status", "normalization_status", "failed_targets", "errors",
        "caveats", "production_current_state", "realtime_guaranteed", "trading_signal",
        "generated_artifact_promoted", "frontend_published",
    ]}
    ledger_files = [name for name in ARTIFACT_TYPES if name not in {"evidence_ledger.json"} and (run_path / name).exists()]
    ledger = {
        **base,
        "finalized_at_utc": str(base.get("retrieved_at_utc")),
        "artifacts": [_artifact_entry(run_path, name, "m5b_finalizer") for name in sorted(ledger_files)],
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
    return candidate


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args(argv)
    try:
        candidate = build(args.run_dir)
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
