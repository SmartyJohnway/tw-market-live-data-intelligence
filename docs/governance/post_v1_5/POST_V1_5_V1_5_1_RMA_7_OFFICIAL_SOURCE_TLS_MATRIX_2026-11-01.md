# Post-v1.5 v1.5.1 RMA-7 — Official-source / TLS Matrix

Date: 2026-11-01
Disposition: **PASS / CLOSED**
Defect closure: **RMA-D001 = CLOSED_PASS**
Next boundary: **RMA-8 — Result / Audit / evidence integrity — NEXT_UNDECIDED / NOT_STARTED**

## 1. Scope and acceptance

RMA-7 classified the production official-source families used by executable routes under the supported Windows / CPython runtime without weakening TLS security.

The exercised inventory contains 23 source cases spanning TWSE MIS, TWSE OpenAPI and official EOD, TWSE historical data, MOPS CSV/JSON/OpenAPI, TPEx official sources, TAIFEX, Phase-H routes, market-state routes and institutional-flow routes.

Acceptance required a governed usable route, certificate verification, hostname verification, bounded HTTP/source behavior, product parser/schema qualification and no silent insecure fallback.

## 2. RMA-7A through 7D evidence

7A established the exact 23-source production inventory.
7B reproduced cold Python/OpenSSL certificate-chain failures source-by-source.
7C proved Windows-native and explicit certifi verified TLS could reach representative hosts while cold default Python trust remained incomplete.
7D reproduced the Windows trust-store mutation deterministically in two fresh Sandboxes and qualified bundled `certifi==2026.7.22` against the complete 23-source inventory.

Certifi CA SHA-256: `9cc2a774b5198dcff14d9be1e66091f538975d867ce029a96bce15a55dfd730f`.
7D concluded `ROOT_CAUSE_PROVEN / REPAIR_QUALIFIED` before product repair was authorized.
## 3. RMA-D001 bounded repair

Owner authorization: `USER_CHAT_2026-11-01_BOUNDED_REPAIR_RMA_D001`.

Runtime repair scope:
- `scripts/ssl_policy.py`
- `scripts/m8a_twse_official_eod_adapter.py`
- `scripts/m8a_tpex_official_eod_adapter.py`
- `scripts/m8r_06_03_production_adapter.py`
- `server/services/phase_i_i1_production_candidate.py`
- `server/services/phase_i_i2_production_transport.py`
- `server/services/phase_i_i3_production_transport.py`

Strict and compatibility TLS now use the governed bundled certifi CA file as deterministic trust material. Strict retains OpenSSL strict verification flags; compatibility uses the same CA base and only removes `VERIFY_X509_STRICT`. `CERT_REQUIRED` and hostname verification remain enabled. Unsafe-explicit behavior is unchanged. No silent fallback was added.

Dedicated pre-fix regression reproduced four D001 failures; the same tests passed after repair. Direct affected regression: **110/110 PASS**. Broader source/transport regression after governance supersession: **220 PASS / 1 skip / 1 unrelated README static-text failure**.

The remaining README failure is the pre-existing `Data and source caveats` phrase assertion and does not execute or inspect D001 TLS/source code.
## 4. Package-level cold repair retest

Noncanonical diagnostic Native ZIP SHA-256:
`F4B8049B4614C0ED2C4F0799315F0810CC2AE029CEA39FE2F857A8131881D333`.
It is diagnostic evidence only and is not release authority.

Fresh cold Windows Sandbox evidence:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-7\7E-d001-bounded-repair\attempt-01-cold-production-matrix\`.

Before any Windows-native HTTPS priming, all 23 inventory cases used their declared production TLS policy exactly once. Results:
- production usable: **23/23**
- product parser/schema PASS: **23/23**
- certificate verification retained: **23/23**
- hostname verification retained: **23/23**
- zero retry: **23/23**
- explicit verified SSL context: **23/23**
- strict/compatibility flag semantics: **PASS**
- classification: `PRODUCTION_ROUTE_USABLE` for **23/23**

Sandbox guest status was PASS. JIT final status was `PASS_RESTORED`; current Sandbox runtime/server count is zero and the JIT active marker is absent.

## 5. Historical activation supersession

The historical Phase-I I1 activation authority remains unchanged. The authorized D001 change to `phase_i_i1_production_candidate.py` is governed by `POST_V1_5_V1_5_1_RMA_D001_I1_LIVE_TESTED_SUPERSESSION_2026-11-01.json`, which verifies exact historical and post-repair SHA-256 values. The activation validator continues to fail closed for any other live-tested delta.

## 6. Final decision

RMA-D001 is **CLOSED_PASS** and is no longer a v1.5.1 release blocker. RMA-7 is **PASS / CLOSED**.

No commit, push, tag, release, VERSION mutation, Stable installation repoint, Secure MCP Tunnel mutation or evidence deletion is authorized or performed by this closure.