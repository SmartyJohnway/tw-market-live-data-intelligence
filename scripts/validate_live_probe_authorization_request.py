"""Validate M5A bounded controlled live-probe authorization requests.

Default CLI behavior is check-only: it reads local files, writes nothing, and performs no network calls.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs/authorization/live_probe_authorization_request_schema.json"
REGISTRY_PATH = ROOT / "docs/source_registry/source_authority_registry.json"
ALLOWED_OUTPUT_PREFIX = Path("research/live_probe_runs/m5b")
FORBIDDEN_OUTPUT_PREFIXES = (
    "frontend/public",
    "research/generated",
    "production",
    "prod",
)
FORBIDDEN_FLAGS = (
    "network_authorized",
    "live_probe_authorized",
    "production_write",
    "frontend_publication",
    "generated_artifact_write",
    "full_market_scan",
    "trading_signal",
    "authorization_token_issued",
)
CONTROLLED_RUNNERS = {
    "scripts/run_m5b_controlled_live_probe.py": {"supports_output_dir": True, "output_root": "research/live_probe_runs/m5b"},
    "scripts/run_m3g04_controlled_live_probe.py": {"supports_output_dir": False, "output_root": "research/live_probe_runs/m3g_04"},
}
FORBIDDEN_SCRIPTS = {
    "scripts/run_all_probes.py",
}
SOURCE_TARGET_MAP = {
    "TWSE_OpenAPI": {"2330", "0050", "00929"},
    "TPEx_OpenAPI": {"8069"},
    "TWSE_MIS": {"2330", "0050", "00929", "8069", "TAIEX"},
    "Yahoo_Finance": {"2330", "0050", "00929", "8069", "TAIEX"},
}
WILDCARDS = {"*", "ALL", "all", "FULL_MARKET", "full_market", "market", "universe"}


def _json_error(code: str, path: str, message: str, **extra: Any) -> dict[str, Any]:
    error = {"code": code, "path": path, "message": message}
    error.update(extra)
    return error


def _load_json(path: Path) -> tuple[Any | None, list[dict[str, Any]]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [_json_error("file_not_found", "$", f"file not found: {path}")]
    except json.JSONDecodeError as exc:
        return None, [_json_error("malformed_json", "$", "request JSON is malformed", line=exc.lineno, column=exc.colno)]
    except OSError as exc:
        return None, [_json_error("file_read_error", "$", str(exc))]


def _parse_dt(value: Any, path: str, errors: list[dict[str, Any]]) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(_json_error("invalid_datetime", path, "datetime must be RFC3339/date-time parseable"))
        return None
    if parsed.tzinfo is None:
        errors.append(_json_error("datetime_timezone_required", path, "datetime must include timezone"))
        return None
    return parsed.astimezone(timezone.utc)


def _registry_source(source_id: Any, registry: dict[str, Any]) -> dict[str, Any] | None:
    for source in registry.get("sources", []):
        if source.get("source_id") == source_id:
            return source
    return None


def _is_relative_safe(path_text: str) -> bool:
    path = Path(path_text)
    drive = getattr(path, "drive", "")
    return not path.is_absolute() and not drive and not re.match(r"^[A-Za-z]:[\\/]", path_text) and ".." not in path.parts and not path_text.startswith(("/", "\\"))


def _normalize_script_path(script: str) -> str | None:
    raw = script.strip()
    path = Path(raw)
    if path.is_absolute() or getattr(path, "drive", "") or re.match(r"^[A-Za-z]:[\\/]", raw) or ".." in path.parts or raw.startswith(("/", "\\")):
        return None
    if raw.startswith("./"):
        raw = raw[2:]
    return raw


def _result_envelope(errors: list[dict[str, Any]], result: str) -> dict[str, Any]:
    return {
        "ok": not errors and result == "ready_for_user_authorization_review",
        "errors": errors,
        "result": result,
        "live_probe_authorized": False,
        "authorization_token_issued": False,
        "execution_performed": False,
        "writes": False,
        "network_used": False,
    }


def validate_request(request: Any, schema: dict[str, Any], registry: dict[str, Any], now: datetime | None = None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(request), key=lambda e: list(e.path)):
        path = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in err.path)
        errors.append(_json_error("schema_validation_failed", path, err.message))
    if not isinstance(request, dict):
        return errors or [_json_error("request_not_object", "$", "request must be a JSON object")]

    requested_at = _parse_dt(request.get("requested_at"), "$.requested_at", errors)
    expires_at = _parse_dt(request.get("expires_at"), "$.expires_at", errors)
    now = now or datetime.now(timezone.utc)
    if requested_at and expires_at:
        if expires_at <= requested_at:
            errors.append(_json_error("expires_not_after_requested_at", "$.expires_at", "expires_at must be after requested_at"))
        if expires_at <= now:
            errors.append(_json_error("request_expired", "$.expires_at", "authorization request is expired"))

    source = _registry_source(request.get("source_id"), registry)
    if source is None:
        errors.append(_json_error("source_not_in_registry", "$.source_id", "source_id must exist in source registry"))
    elif source.get("live_probe_authorization_required") is not True:
        errors.append(_json_error("source_not_live_probe_authorization_required", "$.source_id", "source must require live probe authorization"))
    if source is not None:
        if sorted(request.get("source_risk_flags", [])) != sorted(source.get("risk_flags", [])):
            errors.append(_json_error("source_risk_flags_mismatch", "$.source_risk_flags", "source risk flags must match source registry exactly", expected=source.get("risk_flags", [])))
        if sorted(request.get("required_caveats", [])) != sorted(source.get("required_caveats", [])):
            errors.append(_json_error("required_caveats_mismatch", "$.required_caveats", "required caveats must match source registry exactly", expected=source.get("required_caveats", [])))

    targets = request.get("targets")
    if isinstance(targets, list):
        if not targets:
            errors.append(_json_error("targets_empty", "$.targets", "targets must be non-empty"))
        if len(targets) > 5:
            errors.append(_json_error("too_many_targets", "$.targets", "at most 5 targets are allowed"))
        if len(targets) != len(set(targets)):
            errors.append(_json_error("duplicate_targets", "$.targets", "targets must be unique"))
        for idx, target in enumerate(targets):
            if target in WILDCARDS:
                errors.append(_json_error("wildcard_target_forbidden", f"$.targets[{idx}]", "wildcard/full-market target is forbidden"))
        supported = SOURCE_TARGET_MAP.get(request.get("source_id"), set())
        for idx, target in enumerate(targets):
            if target not in supported:
                errors.append(_json_error("source_target_mapping_unresolved", f"$.targets[{idx}]", "target is not resolvable for requested source", source_id=request.get("source_id"), target=target))

    for flag in FORBIDDEN_FLAGS:
        if request.get(flag) is not False:
            errors.append(_json_error("forbidden_flag_must_be_false", f"$.{flag}", f"{flag} must remain false"))

    output = request.get("proposed_output_directory")
    if isinstance(output, str):
        normalized = output.rstrip("/")
        if not _is_relative_safe(normalized):
            errors.append(_json_error("output_path_not_relative_safe", "$.proposed_output_directory", "output path must be a safe relative path"))
        if any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in FORBIDDEN_OUTPUT_PREFIXES):
            errors.append(_json_error("forbidden_output_path", "$.proposed_output_directory", "output path must not target frontend/public, research/generated, production, or prod"))
        allowed = str(ALLOWED_OUTPUT_PREFIX)
        if not (normalized == allowed or normalized.startswith(allowed + "/")):
            errors.append(_json_error("output_path_not_m5b", "$.proposed_output_directory", "output path must be under research/live_probe_runs/m5b/"))

    script = request.get("proposed_probe_script")
    if isinstance(script, str):
        normalized_script = _normalize_script_path(script)
        if normalized_script is None:
            errors.append(_json_error("probe_script_path_not_relative_safe", "$.proposed_probe_script", "proposed script path must be a safe relative path"))
        elif normalized_script in FORBIDDEN_SCRIPTS:
            errors.append(_json_error("forbidden_probe_script", "$.proposed_probe_script", "scripts/run_all_probes.py is forbidden"))
        elif normalized_script not in CONTROLLED_RUNNERS:
            errors.append(_json_error("probe_script_not_controlled_runner", "$.proposed_probe_script", "proposed script must be an existing controlled runner"))
        elif not (ROOT / normalized_script).is_file():
            errors.append(_json_error("probe_script_missing", "$.proposed_probe_script", "controlled runner file does not exist"))
        else:
            runner = CONTROLLED_RUNNERS[normalized_script]
            if runner.get("supports_output_dir") is not True:
                errors.append(_json_error("probe_script_output_dir_unsupported", "$.proposed_probe_script", "proposed runner cannot honor proposed_output_directory", runner_output_root=runner.get("output_root")))
    return errors


def validate_request_file(request_path: Path, schema_path: Path = SCHEMA_PATH, registry_path: Path = REGISTRY_PATH, now: datetime | None = None) -> dict[str, Any]:
    request, load_errors = _load_json(request_path)
    if load_errors:
        return _result_envelope(load_errors, "repair_required")
    schema, schema_errors = _load_json(schema_path)
    registry, registry_errors = _load_json(registry_path)
    if schema_errors or registry_errors:
        return _result_envelope(schema_errors + registry_errors, "blocked")
    errors = validate_request(request, schema, registry, now=now)
    dependency_codes = {"probe_script_missing"}
    result = "blocked" if any(error["code"] in dependency_codes for error in errors) else "repair_required"
    if not errors:
        result = "ready_for_user_authorization_review"
    return _result_envelope(errors, result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an M5A live-probe authorization request without writing files or using network.")
    parser.add_argument("--request", required=True, help="Path to authorization request JSON")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help="Schema path")
    parser.add_argument("--registry", default=str(REGISTRY_PATH), help="Source registry path")
    args = parser.parse_args(argv)
    result = validate_request_file(Path(args.request), Path(args.schema), Path(args.registry))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
