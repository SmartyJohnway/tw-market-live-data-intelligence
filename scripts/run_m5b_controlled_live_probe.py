from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

try:
    from scripts.build_m5b_staging_candidate import build as build_m5b_candidate, finalize as finalize_m5b_run
    from scripts.validate_m5b_execution_authorization import validate_authorization
except ModuleNotFoundError:
    from build_m5b_staging_candidate import build as build_m5b_candidate, finalize as finalize_m5b_run
    from validate_m5b_execution_authorization import validate_authorization
try:
    from scripts.probe_twse_openapi import normalize_twse_openapi_row
except ModuleNotFoundError:
    from probe_twse_openapi import normalize_twse_openapi_row

ALLOWED_TARGETS = ["2330", "0050", "00929"]
ROOT = Path("research/live_probe_runs/m5b")
CONSUMPTION_ROOT = ROOT / "authorization_consumption"
URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
SUCCESS_CONTRACT_STATUSES = {"normalized_pass", "partial_pass"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def classify_retryable_failure(status: int | None = None, exc: BaseException | None = None) -> bool:
    return bool(exc) or status == 429 or (status is not None and 500 <= status <= 599)


def validate_execution_scope(source: str, targets: list[str], output_dir: str) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    path = Path(output_dir)
    if source != "TWSE_OpenAPI":
        errors.append({"code": "source_mismatch", "path": "$.source"})
    if not targets:
        errors.append({"code": "targets_empty", "path": "$.targets"})
    if any(target in ("*", "ALL", "all") for target in targets):
        errors.append({"code": "wildcard_target", "path": "$.targets"})
    if len(targets) != len(set(targets)):
        errors.append({"code": "duplicate_targets", "path": "$.targets"})
    if sorted(targets) != sorted(ALLOWED_TARGETS):
        errors.append({"code": "target_set_mismatch", "path": "$.targets"})
    if path.is_absolute() or ".." in path.parts:
        errors.append({"code": "output_path_unsafe", "path": "$.output_dir"})
    try:
        path.relative_to(ROOT)
    except ValueError:
        errors.append({"code": "output_outside_m5b", "path": "$.output_dir"})
    return errors


def bind_request_and_authorization(auth: str, request: str) -> dict[str, str]:
    import hashlib

    return {
        "request_sha256": hashlib.sha256(Path(request).read_bytes()).hexdigest(),
        "authorization_sha256": hashlib.sha256(Path(auth).read_bytes()).hexdigest(),
    }


def map_authorized_targets(targets: list[str]) -> dict[str, str]:
    return {target: target for target in targets}


def redact_and_bound_response(data: Any, targets: list[str]) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise ValueError("TWSE_OpenAPI response must be a JSON array")
    bounded = []
    for row in data:
        if not isinstance(row, dict):
            continue
        if str(row.get("Code", "")).strip() in targets:
            bounded.append(row)
    return bounded


def _roc_date_to_iso(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    if len(text) != 7 or not text.isdigit():
        return None
    year = int(text[:3]) + 1911
    month = int(text[3:5])
    day = int(text[5:7])
    try:
        return datetime(year, month, day, tzinfo=timezone.utc).date().isoformat()
    except ValueError:
        return None


def _freshness_assessment(rows: list[dict[str, Any]], retrieved_at_utc: str) -> dict[str, Any]:
    iso_dates = sorted({d for d in (_roc_date_to_iso(row.get("trade_date")) for row in rows) if d})
    latest = iso_dates[-1] if iso_dates else None
    age_days = None
    if latest:
        retrieved_date = datetime.fromisoformat(retrieved_at_utc).date()
        age_days = (retrieved_date - datetime.fromisoformat(latest).date()).days
    return {
        "source_timestamp": latest,
        "source_trade_dates": iso_dates,
        "retrieval_to_source_date_age_days": age_days,
        "freshness_status": "eod_reference" if latest else "unknown_source_date",
        "delay_status": "eod_not_realtime_guaranteed",
        "official_realtime_claim": False,
    }


def _contract_status(rows: list[dict[str, Any]], http_status: int | None, parse_ok: bool, errors: list[dict[str, Any]]) -> str:
    if http_status != 200:
        return "http_failed"
    if not parse_ok:
        return "parse_failed"
    if any(error["code"] in {"normalization_failed", "unauthorized_symbol_in_result", "forbidden_trading_field", "forbidden_realtime_guarantee", "raw_full_payload_retention"} for error in errors):
        return "execution_failed"
    if not rows:
        return "source_empty"
    if len(rows) == len(ALLOWED_TARGETS):
        return "normalized_pass"
    return "partial_pass"


def _common_artifact(run_id: str, retained: list[str], http_status: int | None, contract_status: str, parse_status: str, normalization_status: str, errors: list[dict[str, Any]], retrieved_at_utc: str, freshness: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "source_id": "TWSE_OpenAPI",
        "requested_targets": ALLOWED_TARGETS,
        "retained_targets": retained,
        "retrieved_at_utc": retrieved_at_utc,
        "source_timestamp": freshness.get("source_timestamp"),
        "http_status": http_status,
        "contract_status": contract_status,
        "parse_status": parse_status,
        "normalization_status": normalization_status,
        "failed_targets": [target for target in ALLOWED_TARGETS if target not in retained],
        "errors": errors,
        "caveats": [
            "official_eod_reference_source",
            "not_realtime_guaranteed",
            "not_production_current_state",
            "no_full_raw_payload_retained",
        ],
        "production_current_state": False,
        "realtime_guaranteed": False,
        "trading_signal": False,
        "generated_artifact_promoted": False,
        "frontend_published": False,
    }


def _authorization_id(authorization_path: str | Path) -> str:
    return str(_load_json(authorization_path)["authorization_id"])


def _consumption_path(authorization_id: str) -> Path:
    safe = authorization_id.replace("/", "_").replace("..", "_")
    return CONSUMPTION_ROOT / f"{safe}.json"


def _create_consumption_record(auth_path: str, request_path: str, output_dir: str) -> Path:
    auth = _load_json(auth_path)
    path = _consumption_path(auth["authorization_id"])
    CONSUMPTION_ROOT.mkdir(parents=True, exist_ok=True)
    record = {
        "authorization_id": auth["authorization_id"],
        "source_id": "TWSE_OpenAPI",
        "requested_targets": ALLOWED_TARGETS,
        "consumed_at_utc": _utc_now(),
        "status": "started",
        "output_dir": output_dir,
        "request_path": request_path,
        "authorization_path": auth_path,
        "network_attempted": False,
        "production_current_state": False,
        "realtime_guaranteed": False,
        "trading_signal": False,
        "generated_artifact_promoted": False,
        "frontend_published": False,
    }
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def _update_consumption_record(path: Path, **updates: Any) -> None:
    record = _load_json(path)
    record.update(updates)
    record["updated_at_utc"] = _utc_now()
    _write_json(path, record)


def _detect_forbidden_normalized_fields(row: dict[str, Any], row_index: int) -> list[dict[str, Any]]:
    errors = []
    forbidden = {"buy", "sell", "hold", "target_price", "recommendation", "raw_full_response", "full_raw_payload"}
    for key, value in row.items():
        if key in forbidden:
            errors.append({"code": "forbidden_trading_field", "path": f"$.rows[{row_index}].{key}"})
        if key == "realtime_guaranteed" and value is not False:
            errors.append({"code": "forbidden_realtime_guarantee", "path": f"$.rows[{row_index}].{key}"})
    return errors


def build_bounded_probe_result(run_id: str, rows: list[dict[str, Any]], http_status: int | None, contract_status: str, parse_status: str, normalization_status: str, errors: list[dict[str, Any]], retrieved_at_utc: str, freshness: dict[str, Any]) -> dict[str, Any]:
    retained = [str(row.get("symbol")) for row in rows]
    return {
        **_common_artifact(run_id, retained, http_status, contract_status, parse_status, normalization_status, errors, retrieved_at_utc, freshness),
        "rows": rows,
    }


def build_bounded_evidence_entry(run_dir: Path, artifact_name: str, artifact_type: str) -> dict[str, Any]:
    import hashlib

    path = run_dir / artifact_name
    return {
        "artifact_path": str(path),
        "artifact_type": artifact_type,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "produced_by": "scripts/run_m5b_controlled_live_probe.py",
        "promotion_status": {
            "staging_only": True,
            "production_promoted": False,
            "frontend_published": False,
            "generated_artifact_promoted": False,
            "trading_signal": False,
        },
    }


def build_execution_receipt(run_id: str, authorization_path: str, attempts: int, retry_reason: str | None, http_status: int | None, contract_status: str, retained: list[str], errors: list[dict[str, Any]], retrieved_at_utc: str) -> dict[str, Any]:
    auth = _load_json(authorization_path)
    return {
        "run_id": run_id,
        "authorization_id": auth["authorization_id"],
        "authorization_consumed": True,
        "source_id": "TWSE_OpenAPI",
        "requested_targets": ALLOWED_TARGETS,
        "retained_targets": retained,
        "retrieved_at_utc": retrieved_at_utc,
        "http_status": http_status,
        "attempt_count": attempts,
        "retry_reason": retry_reason,
        "contract_status": contract_status,
        "success": contract_status in SUCCESS_CONTRACT_STATUSES,
        "errors": errors,
        "production_current_state": False,
        "realtime_guaranteed": False,
        "trading_signal": False,
        "generated_artifact_promoted": False,
        "frontend_published": False,
    }


def _write_failure_package(args: argparse.Namespace, consumption_path: Path | None, attempts: int, retry_reason: str | None, http_status: int | None, contract_status: str, parse_status: str, errors: list[dict[str, Any]], retrieved_at_utc: str | None = None) -> None:
    retrieved = retrieved_at_utc or _utc_now()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    run_id = out.name
    freshness = {"source_timestamp": None, "source_trade_dates": [], "retrieval_to_source_date_age_days": None, "freshness_status": "unknown_source_date", "delay_status": "not_realtime_guaranteed", "official_realtime_claim": False}
    base = _common_artifact(run_id, [], http_status, contract_status, parse_status, "failed", errors, retrieved, freshness)
    shutil.copyfile(args.authorization, out / "authorization_snapshot.json")
    shutil.copyfile(args.request, out / "request_snapshot.json")
    _write_json(out / "execution_receipt.json", build_execution_receipt(run_id, args.authorization, attempts, retry_reason, http_status, contract_status, [], errors, retrieved))
    _write_json(out / "bounded_probe_result.json", {**base, "rows": []})
    _write_json(out / "bounded_normalized_rows.json", {**base, "rows": []})
    _write_json(out / "source_contract_assessment.json", {**base, "endpoint": URL, "request_method": "GET", "required_headers": {"Accept": "application/json"}, "required_cookies_or_session": False, "raw_full_response_retention": False})
    _write_json(out / "freshness_delay_assessment.json", {**base, **freshness})
    _write_json(out / "run_summary.json", {**base, "live_probe_executed": True, "live_probe_succeeded": False, "staging_candidate_created": False, "production_promotion_performed": False, "generated_artifacts_refreshed": False, "frontend_published": False, "trading_output_produced": False, "authorization_consumed": True, "retry_count": max(0, attempts - 1), "endpoint": URL})
    try:
        finalize_m5b_run(out, create_candidate=False)
    except Exception as exc:
        _write_json(out / "evidence_ledger.json", {**base, "artifacts": [], "finalization_error": str(exc)})
    if consumption_path:
        _update_consumption_record(consumption_path, status="failed", network_attempted=attempts > 0, attempt_count=attempts, http_status=http_status, contract_status=contract_status, receipt_path=str(out / "execution_receipt.json"), errors=errors)


def write_artifacts(out: Path, auth: str, req: str, attempts: int, retry_reason: str | None, http_status: int | None, rows: list[dict[str, Any]], errors: list[dict[str, Any]], parse_ok: bool, retrieved_at_utc: str) -> str:
    out.mkdir(parents=True, exist_ok=False)
    retained = [str(row.get("symbol")) for row in rows]
    freshness = _freshness_assessment(rows, retrieved_at_utc)
    contract_status = _contract_status(rows, http_status, parse_ok, errors)
    parse_status = "parsed" if parse_ok else "parse_failed"
    normalization_status = "normalized" if rows else ("empty" if contract_status == "source_empty" else "failed")
    shutil.copyfile(auth, out / "authorization_snapshot.json")
    shutil.copyfile(req, out / "request_snapshot.json")
    receipt = build_execution_receipt(out.name, auth, attempts, retry_reason, http_status, contract_status, retained, errors, retrieved_at_utc)
    _write_json(out / "execution_receipt.json", receipt)
    result = build_bounded_probe_result(out.name, rows, http_status, contract_status, parse_status, normalization_status, errors, retrieved_at_utc, freshness)
    _write_json(out / "bounded_probe_result.json", result)
    _write_json(out / "bounded_normalized_rows.json", result)
    base = _common_artifact(out.name, retained, http_status, contract_status, parse_status, normalization_status, errors, retrieved_at_utc, freshness)
    _write_json(out / "source_contract_assessment.json", {**base, "endpoint": URL, "request_method": "GET", "required_headers": {"Accept": "application/json"}, "required_cookies_or_session": False, "raw_full_response_retention": False, "legal_maintenance_risk": "official public OpenAPI; schema drift/rate limits possible", "ai_integration_suitability": "bounded EOD/reference integration only"})
    _write_json(out / "freshness_delay_assessment.json", {**base, **freshness})
    _write_json(out / "run_summary.json", {**base, "live_probe_executed": True, "live_probe_succeeded": contract_status in SUCCESS_CONTRACT_STATUSES, "staging_candidate_created": False, "production_promotion_performed": False, "generated_artifacts_refreshed": False, "frontend_published": False, "trading_output_produced": False, "authorization_consumed": True, "retry_count": max(0, attempts - 1), "endpoint": URL})
    if contract_status in SUCCESS_CONTRACT_STATUSES:
        build_m5b_candidate(out)
    else:
        finalize_m5b_run(out, create_candidate=False)
    return contract_status


def execute(args: argparse.Namespace) -> int:
    consumption_path: Path | None = None
    attempts = 0
    retry_reason = None
    last_status = None
    data: Any = None
    parse_ok = False
    errors: list[dict[str, Any]] = []
    retrieved_at_utc = _utc_now()
    try:
        consumption_path = _create_consumption_record(args.authorization, args.request, args.output_dir)
    except FileExistsError:
        auth_id = _authorization_id(args.authorization)
        print(json.dumps({"ok": False, "errors": [{"code": "authorization_already_consumed", "path": str(_consumption_path(auth_id))}], "network_used": False, "writes": False}, indent=2, sort_keys=True))
        return 1

    try:
        while attempts < args.attempt_count:
            attempts += 1
            _update_consumption_record(consumption_path, status="network_attempt_started", network_attempted=True, attempt_count=attempts)
            try:
                response = requests.get(URL, headers={"Accept": "application/json"}, timeout=10)
                last_status = response.status_code
                retrieved_at_utc = _utc_now()
                if response.status_code == 200:
                    try:
                        data = response.json()
                        parse_ok = True
                    except Exception as exc:
                        errors.append({"code": "json_parse_failed", "detail": str(exc)})
                    break
                errors.append({"code": "http_failed", "detail": f"HTTP {response.status_code}"})
                if not classify_retryable_failure(response.status_code):
                    break
                retry_reason = f"HTTP {response.status_code}"
            except (requests.Timeout, requests.ConnectionError) as exc:
                retrieved_at_utc = _utc_now()
                retry_reason = type(exc).__name__
                errors.append({"code": "retryable_network_failure", "detail": str(exc), "attempt": attempts})
            if attempts >= 2:
                break

        rows: list[dict[str, Any]] = []
        if parse_ok:
            try:
                bounded = redact_and_bound_response(data, ALLOWED_TARGETS)
                now = datetime.fromisoformat(retrieved_at_utc)
                for index, raw in enumerate(bounded):
                    normalized = normalize_twse_openapi_row(raw, now)
                    normalized.pop("raw_row", None)
                    normalized.pop("unmapped_raw_fields", None)
                    errors.extend(_detect_forbidden_normalized_fields(normalized, index))
                    if str(normalized.get("symbol")) not in ALLOWED_TARGETS:
                        errors.append({"code": "unauthorized_symbol_in_result", "path": f"$.rows[{index}].symbol"})
                        continue
                    rows.append(normalized)
            except Exception as exc:
                errors.append({"code": "normalization_failed", "detail": str(exc)})
        if not errors and data is None:
            errors.append({"code": "network_or_http_failed", "detail": f"HTTP {last_status}"})
        contract_status = write_artifacts(Path(args.output_dir), args.authorization, args.request, attempts, retry_reason, last_status, rows, errors, parse_ok, retrieved_at_utc)
        ok = contract_status in SUCCESS_CONTRACT_STATUSES
        try:
            _update_consumption_record(consumption_path, status="succeeded" if ok else "failed", network_attempted=True, attempt_count=attempts, http_status=last_status, contract_status=contract_status, receipt_path=str(Path(args.output_dir) / "execution_receipt.json"), errors=errors)
        except Exception as exc:
            print(json.dumps({"ok": False, "errors": [{"code": "consumption_update_failed_after_finalization", "detail": str(exc), "finalized_package_preserved": True}], "network_used": True}, indent=2, sort_keys=True))
            return 1
        print(json.dumps({"ok": ok, "run_id": Path(args.output_dir).name, "attempt_count": attempts, "retry_reason": retry_reason, "http_status": last_status, "contract_status": contract_status, "retained_targets": [row["symbol"] for row in rows], "network_used": True}, indent=2, sort_keys=True))
        return 0 if ok else 1
    except Exception as exc:
        errors.append({"code": "execution_exception", "detail": str(exc)})
        manifest_path = Path(args.output_dir) / "sha256_manifest.json"
        if manifest_path.exists():
            try:
                manifest_doc = json.loads(manifest_path.read_text())
            except Exception:
                manifest_doc = {}
            if manifest_doc.get("manifest_final") is True:
                print(json.dumps({"ok": False, "errors": errors + [{"code": "finalized_package_preserved", "path": str(manifest_path)}], "network_used": attempts > 0}, indent=2, sort_keys=True))
                return 1
        try:
            _write_failure_package(args, consumption_path, attempts, retry_reason, last_status, "execution_failed", "parse_failed" if not parse_ok else "parsed", errors, retrieved_at_utc)
        finally:
            print(json.dumps({"ok": False, "errors": errors, "network_used": attempts > 0}, indent=2, sort_keys=True))
        return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--acknowledge-bounded-live-probe", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--request")
    parser.add_argument("--source", required=True)
    parser.add_argument("--targets", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--attempt-count", type=int, default=2)
    args = parser.parse_args(argv)
    errors = validate_execution_scope(args.source, args.targets, args.output_dir)
    if not (1 <= args.attempt_count <= 2):
        errors.append({"code": "attempt_count_out_of_range", "path": "$.attempt_count"})
    if not args.authorization:
        errors.append({"code": "missing_authorization", "path": "$.authorization"})
    if not args.request:
        errors.append({"code": "missing_request", "path": "$.request"})
    if args.authorization and args.request:
        errors += validate_authorization(args.authorization, args.request)
    if args.execute_live and not args.acknowledge_bounded_live_probe:
        errors.append({"code": "missing_acknowledgement", "path": "$.acknowledgement"})
    if Path(args.output_dir, "execution_receipt.json").exists():
        errors.append({"code": "reused_output_receipt", "path": "$.output_dir"})
    if args.execute_live and args.authorization:
        try:
            if _consumption_path(_authorization_id(args.authorization)).exists():
                errors.append({"code": "authorization_already_consumed", "path": str(_consumption_path(_authorization_id(args.authorization)))})
        except Exception as exc:
            errors.append({"code": "authorization_consumption_check_failed", "detail": str(exc), "path": "$.authorization"})
    if args.check_only or not args.execute_live or errors:
        print(json.dumps({"ok": not errors, "errors": errors, "network_used": False, "writes": False, "execution_performed": False}, indent=2, sort_keys=True))
        return 0 if not errors else 1
    return execute(args)


if __name__ == "__main__":
    raise SystemExit(main())
