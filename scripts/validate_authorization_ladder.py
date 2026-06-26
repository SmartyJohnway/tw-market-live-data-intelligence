"""Validate M4 authorization ladder state and hypothetical authorization tokens."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.json_schema_validation import validate_json_schema_subset

FORBIDDEN_ACTIONS = {"live_probe", "production_refresh", "frontend_publication", "trading_signal", "full_market_scan", "broker_auth"}
AUTHORIZED_LEVEL_ACTIONS = {
    "local_only": {"local_validation"},
    "fixture_replay": {"local_validation", "fixture_replay"},
    "staging_write_authorized": {"local_validation", "fixture_replay", "staging_write"},
    "controlled_live_probe_authorized": {"local_validation", "fixture_replay", "controlled_live_probe_dry_run"},
    "frontend_publication_authorized": {"local_validation", "fixture_replay", "frontend_publication_dry_run"},
    "production_refresh_authorized": {"local_validation", "fixture_replay", "production_refresh_dry_run"},
}


def _parse_dt(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_authorization_token(token: dict, schema_path: str | Path = "docs/authorization/authorization_token_schema.json", now: datetime | None = None) -> list[dict]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    errors = validate_json_schema_subset(token, schema)
    now = now or datetime.now(timezone.utc)
    try:
        if _parse_dt(token.get("expires_at", "1970-01-01T00:00:00Z")) <= now:
            errors.append({"code": "authorization_token_expired", "path": "$.expires_at"})
    except ValueError:
        errors.append({"code": "authorization_token_invalid_expiry", "path": "$.expires_at"})
    allowed_actions = set(token.get("allowed_actions", []))
    forbidden_actions = set(token.get("forbidden_actions", []))
    forbidden_grants = sorted(allowed_actions & FORBIDDEN_ACTIONS)
    if forbidden_grants:
        errors.append({"code": "token_grants_forbidden_actions", "path": "$.allowed_actions", "actions": forbidden_grants})
    level = token.get("authorization_level", "local_only")
    allowed_for_level = AUTHORIZED_LEVEL_ACTIONS.get(level, set())
    unexpected = sorted(allowed_actions - allowed_for_level - FORBIDDEN_ACTIONS)
    if unexpected:
        errors.append({"code": "token_action_not_allowed_for_level", "path": "$.allowed_actions", "actions": unexpected})
    target = token.get("allowed_target_universe", {})
    if target.get("full_market_scan") is not False:
        errors.append({"code": "token_full_market_scan_forbidden", "path": "$.allowed_target_universe.full_market_scan"})
    if token.get("output_path_policy") not in {"safe_tmp_only", "operator_safe_path_only"}:
        errors.append({"code": "token_output_path_policy_invalid", "path": "$.output_path_policy"})
    for flag in ("no_trading_signal", "no_realtime_guarantee", "no_production_write"):
        if token.get(flag) is not True:
            errors.append({"code": "token_safety_flag_must_be_true", "path": f"$.{flag}"})
    return errors


def validate_authorization_ladder(state: dict | None = None, token: dict | None = None) -> list[dict]:
    state = state or {}
    errors = []
    if any(state.get(k) for k in ["live_probe_authorized", "production_refresh_authorized", "frontend_publication_authorized"]):
        errors.append({"code": "unauthorized_elevation", "path": "$"})
    if token is not None:
        errors.extend(validate_authorization_token(token))
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    token = json.loads(Path(args.token).read_text(encoding="utf-8")) if args.token else None
    errors = validate_authorization_ladder({}, token)
    result = {"ok": not errors, "errors": errors, "current_repo_state": "local-only", "live_probe_authorized": False, "production_refresh_authorized": False, "frontend_publication_authorized": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
