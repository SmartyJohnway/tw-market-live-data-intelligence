# M6F Hotfix — Frontend Watchlist ID and FastAPI SSL Policy Resolution

## Real local clone issue

Actual local clone-and-run testing found two operator-blocking issues in the M6 local workbench path:

1. The readonly preview frontend reconstructed watchlist JSON from editable table rows without the required M5N `id` field.
2. The FastAPI live-observation endpoint validated a missing `ssl_policy` query parameter directly as `strict`, bypassing the explicit `TW_MARKET_SSL_POLICY` environment override path.

This hotfix is intentionally small and does not change M5F canonical artifacts, observation semantics, source-health semantics, conversation semantics, or trading behavior.

## Frontend id repair

`frontend/readonly-preview/m5k-workbench.js` now derives stable item IDs when rebuilding watchlist JSON from rows:

- `category` is the trimmed category field, falling back to `custom`.
- `symbol` is trimmed and upper-cased.
- `id` is `${category}:${symbol}`.

The repair keeps generated payloads compatible with backend `validate_watchlist()` and prevents fail-closed invalid watchlist errors caused by missing `id` fields.

## FastAPI resolve_ssl_policy repair

`server/main.py` now calls `resolve_ssl_policy(ssl_policy)` for `/api/m5k/live-observation/execute`.

This preserves the intended policy order:

1. Query parameter / explicit request policy wins when present.
2. `TW_MARKET_SSL_POLICY` is honored when the query parameter is absent.
3. Strict TLS remains the default when neither query nor environment override is present.
4. Invalid query or environment values fail closed with `400 invalid_ssl_policy` before live observation execution.

## Why the server does not auto-set compatibility

The server does not set `TW_MARKET_SSL_POLICY=compatibility`, does not mutate `os.environ`, and does not silently downgrade TLS policy. Compatibility mode remains an explicit operator decision through either the request parameter or environment variable. Unsafe mode remains explicit only via `unsafe-explicit`.

## Tests added

- Frontend static/contract regression that verifies `watchlistFromRows()` generates `id: ${category}:${symbol}`, upper-cases symbols, uses `custom` category fallback, and that an equivalent payload passes backend `validate_watchlist()`.
- FastAPI endpoint tests that monkeypatch environment policy and `_m5k_execute_live_observation` to avoid network calls while asserting policy resolution and invalid-policy fail-closed behavior.

## Validation commands

- `python -m compileall scripts server tests`
- `pytest -m "not network" -v`
- `python scripts/run_m6e_operator_acceptance.py --check-only`
- `python scripts/run_operator_preflight.py --json --timeout-seconds 300`
- `python server/mcp_server.py --startup-check`
- `python scripts/governance_forbidden_path_guard.py`
- `python scripts/forbidden_behavior_scanner.py`
- `git diff --check`

## Forbidden behavior confirmation

- No M5F mutation.
- No observation semantic change.
- No source-health semantic change.
- No conversation semantic change.
- No polling, scheduler, or startup network behavior.
- No full-market scan.
- No broker/auth, ranking, target price, buy/sell/hold, or trading recommendation behavior.
- No raw payload leakage.
- No silent TLS fallback.
- No automatic server-side compatibility default.
