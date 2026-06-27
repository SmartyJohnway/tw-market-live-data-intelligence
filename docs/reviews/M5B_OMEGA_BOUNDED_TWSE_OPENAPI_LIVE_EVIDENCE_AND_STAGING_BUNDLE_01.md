# M5B Omega bounded TWSE OpenAPI live evidence and staging bundle 01

Final status: pass

## Authorization

- Authorization ID: `m5b-twse-openapi-2330-0050-00929-20260627-user-bounded-01`
- Authorized by: user
- Authorized at UTC: `2026-06-27T00:00:00Z`
- Expires at UTC: `2026-06-28T00:00:00Z`
- Single use: true
- Allowed source: TWSE_OpenAPI
- Allowed targets: 2330, 0050, 00929

## Live execution

- Live probe executed: true
- Live probe succeeded: true
- Endpoint used: `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`
- HTTP status: 200
- Attempt count: 1
- Retry reason: none
- Targets returned: 0050, 00929, 2330
- Failed targets: none
- Contract status: `normalized_pass`
- Freshness/delay status: EOD/reference semantics preserved; realtime is not guaranteed.

## Staging and forbidden outputs

- Staging candidate created: true
- Production promotion performed: false
- Generated artifacts refreshed: false
- Frontend published: false
- Trading output produced: false
- Authorization consumed: true
- Other sources probed: false

## Artifact directory

`research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z/`

The SHA-256 manifest status is `pass`. No full raw exchange payload and no non-target rows were retained.

## Remaining blockers

M5C staging promotion, frontend publication, production refresh, and any trading/recommendation workflows remain unauthorized and blocked pending a separate authorization.

## Repair follow-up

- Added global single-use authorization consumption at `research/live_probe_runs/m5b/authorization_consumption/<authorization_id>.json`; changing `--output-dir` can no longer reuse the same authorization.
- Added structured failure handling so post-network JSON, normalization, HTTP, and artifact failures emit consumed failure receipts and return non-zero for failed contract statuses.
- Added deterministic staging finalization: staging candidate, run summary, evidence ledger, and SHA-256 manifest are now produced by `scripts/build_m5b_staging_candidate.py` without manual artifact edits.
- Populated evidence ledger entries with artifact path, type, SHA-256, lineage, producer, and promotion status.
- Replaced empty failure-injection tests with assertions for malformed payloads, unauthorized symbols, raw full-payload retention, trading fields, realtime guarantees, and single-use authorization reuse.
- Computed `source_timestamp=2026-06-26` from ROC trade date `1150626`, with retrieval-to-source date age of 1 day.

## Second repair follow-up

- Failure finalization no longer creates `staging_candidate.json`; candidate creation is restricted to `normalized_pass` and `partial_pass` contract statuses.
- Final manifests are immutable by default: rerunning the staging builder against a finalized run now fails unless an explicit maintenance override is provided.
- Added `scripts/verify_m5b_manifest.py` to recalculate artifact SHA-256 values and detect tampered, missing, or untracked artifacts.
- Added mocked full `execute()` flow tests for HTTP 400 failure and consumed-authorization reuse, confirming non-zero return and zero network calls on reuse.
- Evidence ledger entries now distinguish `produced_by` from `cataloged_by` so runner-produced artifacts are not misattributed to the finalizer.
