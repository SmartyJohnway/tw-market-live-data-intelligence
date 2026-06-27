# M5A Bounded Controlled Live Probe Authorization Package Preflight

Conclusion: `ready_for_user_authorization_review`

## Scope

This review adds a machine-verifiable request schema, validator, fixture simulation, and documentation for a future M5B bounded single-source live probe authorization decision.

## Safety outcome

- `live_probe_authorized=false`
- `authorization_token_issued=false`
- `execution_performed=false`
- No market-data live request was performed.
- No production write was performed.
- No frontend/public write was performed.
- No research/generated write was performed.
- No full-market scan was performed.
- No trading or recommendation output was produced.

## Added artifacts

- `docs/authorization/live_probe_authorization_request_schema.json`
- `docs/authorization/LIVE_PROBE_AUTHORIZATION_PACKAGE.md`
- `docs/authorization/M5A_SOURCE_CANDIDATE_DECISION_MATRIX.md`
- `scripts/validate_live_probe_authorization_request.py`
- `tests/fixtures/authorization/valid_m5a_live_probe_request.json`
- `tests/fixtures/authorization/invalid_m5a_live_probe_requests.json`
- `tests/unit/test_m5a_live_probe_authorization_request.py`

## Validator guarantees

The validator checks JSON Schema Draft 2020-12 with `FormatChecker`, request/expiry dates, source registry presence, `live_probe_authorization_required=true`, registry-aligned caveats and risk flags, source-specific target mapping, uniqueness and bounded target count, forbidden flags, safe M5B output path, absolute/traversal script path rejection, and controlled-runner script selection. It also rejects runners that cannot honor the requested M5B output directory.

Malformed JSON returns structured errors and does not traceback.

## Repair addressed

The M5A request now proposes `scripts/run_m5b_controlled_live_probe.py`, an interface/preflight runner that explicitly accepts `--output-dir` under `research/live_probe_runs/m5b/` and performs no network execution or writes. The older M3G04 runner remains detectable as incompatible because it writes under `research/live_probe_runs/m3g_04/`.

## Recommended first M5B candidate

`TWSE_OpenAPI` is the recommended first M5B candidate because it is official, lower risk, single-source, and can resolve the TWSE-listed bounded targets `2330`, `0050`, and `00929`.

This recommendation is not authorization.
