from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = Path('docs/authorization/m5b_live_probe_execution_authorization_schema.json')
TARGETS = ['2330', '0050', '00929']


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def _receipt_time(receipt_doc: dict) -> datetime | None:
    for key in ('retrieved_at_utc', 'consumed_at_utc', 'executed_at_utc'):
        value = receipt_doc.get(key)
        if value:
            return _dt(str(value))
    return None


def validate_authorization(authorization, request, receipt=None, now=None, mode: str | None = None):
    """Validate M5B authorization.

    Modes:
    - execution_preflight: authorization must be unexpired at `now`.
    - receipt_audit: authorization is audited against the receipt execution time;
      current wall-clock expiry is intentionally ignored for historical reproducibility.
    """
    errors = []
    mode = mode or ('receipt_audit' if receipt else 'execution_preflight')
    if mode not in {'execution_preflight', 'receipt_audit'}:
        return [{'code': 'invalid_validation_mode', 'path': '$.mode', 'detail': mode}]
    try:
        auth = _load_json(authorization)
    except Exception as exc:
        return [{'code': 'authorization_read_failed', 'detail': str(exc), 'path': '$'}]
    schema = _load_json(SCHEMA)
    for err in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(auth):
        errors.append({'code': 'schema_error', 'path': '$' + ''.join(f'/{x}' for x in err.path), 'detail': err.message})
    if errors:
        return errors

    receipt_doc = None
    if receipt:
        try:
            receipt_doc = _load_json(receipt)
        except Exception as exc:
            errors.append({'code': 'receipt_read_failed', 'detail': str(exc), 'path': '$.receipt'})
            return errors

    try:
        authorized_at = _dt(auth['authorized_at_utc'])
        expires_at = _dt(auth['expires_at_utc'])
        if expires_at <= authorized_at or (expires_at - authorized_at).total_seconds() > 86400:
            errors.append({'code': 'invalid_24h_expiry', 'path': '$.expires_at_utc'})
        if mode == 'execution_preflight':
            comparison_now = now or datetime.now(timezone.utc)
            if comparison_now < authorized_at:
                errors.append({'code': 'authorization_not_yet_valid', 'path': '$.authorized_at_utc'})
            if comparison_now >= expires_at:
                errors.append({'code': 'authorization_expired', 'path': '$.expires_at_utc'})
        else:
            if receipt_doc is None:
                errors.append({'code': 'receipt_required_for_audit', 'path': '$.receipt'})
            else:
                executed_at = _receipt_time(receipt_doc)
                if executed_at is None:
                    errors.append({'code': 'receipt_timestamp_missing', 'path': '$.receipt'})
                elif not (authorized_at <= executed_at < expires_at):
                    errors.append({'code': 'receipt_outside_authorization_window', 'path': '$.receipt.retrieved_at_utc'})
    except Exception as exc:
        errors.append({'code': 'timestamp_parse_failed', 'detail': str(exc), 'path': '$.authorized_at_utc'})

    if auth.get('request_sha256') != sha256_file(request):
        errors.append({'code': 'request_sha256_mismatch', 'path': '$.request_sha256'})
    if sorted(auth.get('allowed_targets', [])) != sorted(TARGETS):
        errors.append({'code': 'target_set_mismatch', 'path': '$.allowed_targets'})
    forbidden = ['production_write', 'frontend_publication', 'generated_artifact_write', 'full_market_scan', 'trading_signal', 'source_fallback_allowed', 'raw_full_response_retention']
    for key in forbidden:
        if auth.get(key) is not False:
            errors.append({'code': 'forbidden_flag_not_false', 'path': '$.' + key})
    if receipt_doc is not None:
        if receipt_doc.get('authorization_id') != auth.get('authorization_id'):
            errors.append({'code': 'receipt_authorization_mismatch', 'path': '$.authorization_id'})
        if receipt_doc.get('authorization_consumed') is not True:
            errors.append({'code': 'authorization_not_consumed', 'path': '$.authorization_consumed'})
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--authorization', required=True)
    parser.add_argument('--request', required=True)
    parser.add_argument('--receipt')
    parser.add_argument('--mode', choices=['execution_preflight', 'receipt_audit'])
    args = parser.parse_args(argv)
    errors = validate_authorization(args.authorization, args.request, args.receipt, mode=args.mode)
    print(json.dumps({'ok': not errors, 'errors': errors, 'network_used': False, 'writes': False}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
