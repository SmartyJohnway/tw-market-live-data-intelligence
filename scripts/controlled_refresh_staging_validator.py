"""Fail-closed validator for fixture-backed controlled refresh staging payloads."""
from __future__ import annotations

FORBIDDEN_KEYS = {"buy", "sell", "hold", "target_price", "score", "rank", "recommendation", "realtime_guaranteed", "official_realtime"}
ALLOWED_SOURCE_IDS = {"TWSE_OpenAPI", "TPEx_OpenAPI", "TWSE_MIS", "Yahoo_Finance"}
FRESHNESS = {"live_candidate", "delayed", "stale", "eod_batch", "unknown"}
DELAY = {"not_delayed_candidate", "delayed_candidate", "stale", "eod", "unknown"}
TOP = {"schema_version", "generated_at_utc", "staging_only", "operator_confirmations", "target_universe", "source_runs", "validation"}
RUN = {"source_id", "source_type", "authority_level", "request_method", "url_or_fixture", "http_status", "contract_status", "retrieved_at_utc", "source_timestamp", "freshness_status", "delay_status", "staleness_seconds", "normalization_status", "data_quality_flags", "source_risk_flags", "normalized_sample_preview", "raw_evidence_ref", "errors"}
FALSE_FLAGS = {"network_authorized", "production_write", "frontend_write", "generated_artifact_write", "full_market_scan", "trading_signal"}
FULL_MARKET_TARGET_VALUES = {"full_market", "all", "*"}
TWSE_MIS_UNOFFICIAL_RISK_ALIASES = {"unofficial_source_risk", "unofficial_endpoint", "unofficial_frontend_endpoint"}


def _walk(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def validation_error(code: str, path: str, message: str) -> dict:
    return {"code": code, "path": path, "message": message}


def validate_controlled_refresh_staging_payload(payload: dict) -> list[dict]:
    errors: list[dict] = []
    if not isinstance(payload, dict):
        return [validation_error("invalid_payload", "$", "payload must be an object")]
    for field in sorted(TOP - payload.keys()):
        errors.append(validation_error("missing_top_level_field", f"$.{field}", "required top-level field missing"))
    if payload.get("staging_only") is not True:
        errors.append(validation_error("staging_only_required", "$.staging_only", "staging_only must be true"))
    validation = payload.get("validation", {})
    if not isinstance(validation, dict):
        errors.append(validation_error("invalid_validation", "$.validation", "validation must be an object"))
        validation = {}
    for flag in sorted(FALSE_FLAGS):
        if validation.get(flag) is not False:
            errors.append(validation_error("governance_flag_must_be_false", f"$.validation.{flag}", f"{flag} must be false"))
    target = payload.get("target_universe", {})
    if isinstance(target, dict):
        for field in ("scope", "mode"):
            if target.get(field) in FULL_MARKET_TARGET_VALUES:
                errors.append(validation_error("full_market_target_forbidden", f"$.target_universe.{field}", "full-market target universe is forbidden"))
    if isinstance(target, dict) and target.get("full_market_scan") is True:
        errors.append(validation_error("full_market_target_forbidden", "$.target_universe.full_market_scan", "full-market scan is forbidden"))
    runs = payload.get("source_runs", [])
    if not isinstance(runs, list):
        errors.append(validation_error("invalid_source_runs", "$.source_runs", "source_runs must be a list"))
        runs = []
    for i, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(validation_error("invalid_source_run", f"$.source_runs[{i}]", "source_run must be an object"))
            continue
        for field in sorted(RUN - run.keys()):
            errors.append(validation_error("missing_source_run_field", f"$.source_runs[{i}].{field}", "required source_run field missing"))
        if run.get("source_id") not in ALLOWED_SOURCE_IDS:
            errors.append(validation_error("source_id_not_allowed", f"$.source_runs[{i}].source_id", "source_id is not allowlisted"))
        if run.get("freshness_status") not in FRESHNESS:
            errors.append(validation_error("invalid_freshness_status", f"$.source_runs[{i}].freshness_status", "invalid freshness_status"))
        if run.get("delay_status") not in DELAY:
            errors.append(validation_error("invalid_delay_status", f"$.source_runs[{i}].delay_status", "invalid delay_status"))
        if run.get("source_id") == "TWSE_MIS" and TWSE_MIS_UNOFFICIAL_RISK_ALIASES.isdisjoint(set(run.get("source_risk_flags", []))):
            errors.append(validation_error("missing_unofficial_source_risk", f"$.source_runs[{i}].source_risk_flags", "TWSE_MIS must preserve an unofficial-source risk flag"))
    for path, key, _ in _walk(payload):
        if str(key).lower() in FORBIDDEN_KEYS:
            errors.append(validation_error("forbidden_field", f"{path}.{key}", "trading signal or realtime guarantee field is forbidden"))
    return errors
