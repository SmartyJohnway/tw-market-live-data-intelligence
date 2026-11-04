# Post-v1.5 v1.5.1 RMA-5 — Identity Resolution Matrix

Date: 2026-11-01
Disposition: **PASS / CLOSED**

## 1. Authority and scope

RMA-5 is governed by
`POST_V1_5_V1_5_1_RMA_TEST_CONTRACT_2026-10-31.md`.

Required coverage is: code, `MARKET:CODE`, ISIN, Chinese name, at least one TPEx
common share, at least one non-common-share instrument family, nonexistent
identity, and ambiguity where available.

Acceptance requires canonical target, market, ISIN, instrument family/type and
execution eligibility to agree with the current Security Master, with fail-closed
behavior for unsupported identity or eligibility.

RMA-5 is identity-only. It does not authorize RMA-6 capability execution or
RMA-7 provider/TLS acquisition.

## 2. Candidate and Security Master under test

Candidate HEAD: `b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c`
`VERSION`: `1.5.0`

Security Master release:
`security-master-20261101T050353Z`
Active index facts used by the matrix:

- record count: `54,842`
- execution-eligible count: `2,204`
- active index SHA-256:
  `f33606cc1d851b3dfb022880c54e17fcca86ff213e27fcabfd7110c568f79cac`
- active manifest SHA-256:
  `9b3fecb3b8d285006b5ecff53ec5e790fd0951bc10c0812f4538cfdd3640c218`

The public path under test was the candidate Native Local Service plus the public
MCP `market_validate_request` / `market_preview_request` surface. No internal
resolver shortcut was used for acceptance.

## 3. Evidence lineage

Preserved RMA-5 evidence root:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-5\`

- `attempt-01-identity-matrix` — preflight-only harness issue `RMA-D009`;
  no formal product matrix was executed.
- `attempt-02-identity-matrix-clean` — product behavior was correct, but the
  blocked-warrant acceptance predicate was wrong; recorded as `RMA-D010`.
- `attempt-03-identity-matrix-clean` — clean acceptance retest and closure proof.

No prior attempt evidence was deleted or overwritten.
## 4. Clean attempt-03 matrix

| Case | Input | Result | Canonical / classification | Eligibility |
|---|---|---|---|---|
| Code | `2330` | resolved | `TWSE:2330`, common share | allowed |
| MARKET:CODE | `TWSE:2330` | resolved | `TWSE:2330`, common share | allowed |
| ISIN | `TW0002330008` | resolved | `TWSE:2330`, common share | allowed |
| Chinese name | `台積電` | resolved | `TWSE:2330`, common share | allowed |
| TPEx common share | `TPEX:5227` | resolved | `TPEX:5227`, company_share/common_share | allowed |
| Non-common family | `TWSE:00400A` | resolved | `fund_product/etf` | allowed |
| Known unsupported type | `TWSE:03006X` | `unsupported_security_type` | `derivative/warrant` | blocked |
| Nonexistent | `TWSE:999999` | `not_found` | no canonical identity | not eligible |

Cross-form consistency for `TWSE:2330`:

- market: `TWSE`
- ISIN: `TW0002330008`
- family/type: `company_share/common_share`
- execution eligibility: `allowed`

TPEx sample `TPEX:5227` resolved with ISIN `KYG0100G1064` and
`company_share/common_share` classification.

ETF sample `TWSE:00400A` resolved with ISIN `TW00000400A3` and
`fund_product/etf` classification.
## 5. Fail-closed behavior

Known warrant `TWSE:03006X` was not treated as unknown. The product returned its
canonical identity, market, ISIN `TW14Z03006X7`, family/type
`derivative/warrant`, and execution eligibility `blocked` with reason
`unsupported_instrument_type`.

Its validation status was `unsupported`, resolution status was
`unsupported_security_type`, and preview status was `target_not_plannable`.
No network execution or evidence execution occurred.

Nonexistent `TWSE:999999` returned `not_found`, no canonical identity,
`validation_status=invalid`, and `target_not_plannable` preview. No network or
execution occurred.

## 6. Ambiguity availability

The active 54,842-record index was exhaustively scanned across exact canonical
ID, security code, ISIN, Chinese name and English name input tokens.

- distinct exact input tokens: `219,368`
- ambiguous exact-token collisions: `0`
- duplicate Chinese-name collisions: `0`
- cross-market duplicate security-code collisions: `0`

Therefore a natural ambiguity case is not available in the current Security
Master. RMA-5 satisfies the contract's `ambiguity where available` clause by
preserving this exhaustive negative evidence instead of fabricating ambiguity.
## 7. Harness defects and adjudication

`RMA-D009` was a preflight-only PowerShell variable collision: `$home` collided
case-insensitively with read-only `$HOME`. The corrected `$rmaHome` preflight
proved the intended candidate Home, ACTIVE identity release and stopped service.
Status: `CLOSED_PASS`.

`RMA-D010` was an acceptance-predicate error. Attempt-02 expected every known
identity to report `resolved`; the product correctly reports
`unsupported_security_type` when identity is known but execution eligibility is
blocked. Attempt-03 used the contract-correct predicate and passed unchanged
product code. Status: `CLOSED_PASS`.

No RMA-5 product defect was established.

## 8. Clean acceptance result

Attempt-03 public MCP result:

```text
stdio initialize              PASS
code                           PASS
MARKET:CODE                    PASS
ISIN                           PASS
Chinese name                   PASS
TPEx common share              PASS
non-common allowed family      PASS
blocked unsupported warrant    PASS / governed fail-closed
nonexistent identity           PASS / governed fail-closed
failed_checks                  []
```

Disposition: **RMA-5 PASS / CLOSED**.
## 9. Containment and next boundary

Post-test containment:

- candidate service: `NOT_RUNNING`
- candidate service alive: `false`
- Security Master: `ACTIVE`
- active release: `security-master-20261101T050353Z`
- existing Stable `/api/health`: `healthy`
- `git diff --check`: PASS
- HEAD unchanged: `b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c`
- `VERSION` unchanged: `1.5.0`

RMA-5 did not authorize or perform product code changes, version mutation,
commit, push, tag, release, Stable/Tunnel repoint, or provider-network execution.

The next undecided boundary is **RMA-6 — Capability execution matrix**.
RMA-6 requires Validate -> Preview -> explicit authorization -> Execute Once ->
Evidence -> Result -> Audit for executable capability families. It must not begin
merely because RMA-5 is closed; explicit Owner instruction remains required.

`RMA-D001 — Production Evidence TLS Policy Integration` remains open for the
RMA-6/RMA-7 production capability/source-TLS work and does not keep RMA-5 open.
