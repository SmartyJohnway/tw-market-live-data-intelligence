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
