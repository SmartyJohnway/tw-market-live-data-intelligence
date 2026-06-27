# M5A Bounded Controlled Live Probe Authorization Package

Status: `ready_for_user_authorization_review` when the request validator passes.

This package is a preflight-only authorization request format for the next M5B bounded single-source live probe. It does not authorize network access, does not issue a token, and does not execute a live market request.

## Non-negotiable inactive flags

Every valid request must keep these values false:

- `network_authorized=false`
- `live_probe_authorized=false`
- `production_write=false`
- `frontend_publication=false`
- `generated_artifact_write=false`
- `full_market_scan=false`
- `trading_signal=false`
- `authorization_token_issued=false`

## Allowed sources

The M5A request may name only one of these source IDs:

- `TWSE_OpenAPI`
- `TPEx_OpenAPI`
- `TWSE_MIS`
- `Yahoo_Finance`

The validator checks that the source exists in `docs/source_registry/source_authority_registry.json` and that `live_probe_authorization_required=true`.

## Allowed bounded targets

A request must use `target_mode=bounded`, `max_targets=5`, and one to five unique targets from:

- `2330`
- `0050`
- `00929`
- `8069`
- `TAIEX`

Wildcard, empty, full-market, and unknown targets are invalid. Source-specific target mappings must resolve before the request is ready for review.

## Output and runner policy

- Proposed output directory must be under `research/live_probe_runs/m5b/`.
- Proposed output directory must not be under `frontend/public/`, `research/generated/`, `production/`, or `prod/`.
- Proposed script must be an existing controlled runner that can honor the requested `--output-dir`.
- `scripts/run_m3g04_controlled_live_probe.py` is not M5B-ready because it writes to `research/live_probe_runs/m3g_04/`; requests that pair it with `research/live_probe_runs/m5b/` are `repair_required`.
- `scripts/run_m5b_controlled_live_probe.py` is currently an interface/preflight runner only; it validates arguments and output-directory semantics without network execution or writes.
- `scripts/run_all_probes.py` is explicitly forbidden.

## Validation command

```bash
python scripts/validate_live_probe_authorization_request.py \
  --request tests/fixtures/authorization/valid_m5a_live_probe_request.json
```

The default CLI is check-only: no file writes, no network calls, no live probe, and no token issuance.

## Result vocabulary

The package outcome must be exactly one of:

- `ready_for_user_authorization_review`
- `repair_required`
- `blocked`

A ready result is not authorization. It only means the user can review a bounded single-source M5B request.
