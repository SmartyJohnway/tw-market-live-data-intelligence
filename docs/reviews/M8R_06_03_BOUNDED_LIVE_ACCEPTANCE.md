# M8R-06-03 Bounded Live Acceptance

## Result

- code head used for live execution: `e27ffe065beceab76752ec4ae761eefd4355faae`
- status: `PASS_WITH_CAVEATS`
- scope: `TWSE:2330`, `TPEX:5227`, `current_observation`, `official_eod_reference`
- logical operations: `4`
- canonical batch invocations: `4`
- planner network_request_estimate: `4`
- actual bounded source invocations: `4`
- network accounting equal: `true`
- transport: `production_transport`
- test_transport_active: `false`
- authorization: `umea-v1-b723c9ae498a6a7fab68`
- claim: `umecl-v1-710136b60b067bec7f94`
- consumption state: `consumed_success`
- execution receipt: `umerec-v1-b6b50b54cb72119d134a`
- evidence bundle: `umeb-v1-055f771f1b159e543bf8`
- external_market_network_attempted: `true`
- external_market_network_executed: `true`
- automatic retry: `false`
- second authorization: `false`

## Operations

| Target / capability | Source family | Status | Items | SHA256 |
| --- | --- | --- | ---: | --- |
| TWSE:2330 / current_observation | TWSE_MIS | succeeded | 1 | `c61fd92637cd9a248e98c9231bce5d0341319145f1e2d90f4ae4c3481709ebe2` |
| TPEX:5227 / current_observation | TWSE_MIS | succeeded | 1 | `149e56ad869765cfa3bdfcbe8cd31850dff45c8b5069c32b37f640e9c0299c39` |
| TWSE:2330 / official_eod_reference | TWSE_OPENAPI | succeeded | 1 | `054e84fefeea965c0fcc3e205e7d276b6d6fba2fe1bc70c663131a9cc34321aa` |
| TPEX:5227 / official_eod_reference | TPEX_OPENAPI | succeeded | 1 | `9bbe2cd575010b2c2803dedd8ffc488d64e75fda180729ac279de215b8551da8` |

## Caveat

`current_observation` is accepted only as bounded current/live-ish observation evidence. No guaranteed realtime claim is made.
