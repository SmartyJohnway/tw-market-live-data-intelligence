# J-B03-A2.4 — TPEx Disposition Source-Contract Verification

**Disposition:** `J_B03_A2_4_HOLD_LIVE_SOURCE_CONTRACT_INCOMPATIBLE`

**Owner authority:** `USER_CHAT_2026-10-07_J_B03_A2_4_TPEX_DISPOSITION_SOURCE_CONTRACT_VERIFICATION_AUTHORIZATION`

**Starting main:** `51b19b1207413fafeb5b244ae655814df01acda5` / `c94256856361632af9984662d2e2c1dfaaad49cb`

**PR #318:** MERGED / CLOSED

## Static source identity

The current dormant descriptor identifies `H1-TPEX-DISPOSITION-OPENAPI` as
`TPEX_DISPOSITION_OPEN_DATA`, contract `tpex_disposal_information`, Taipei
Exchange, data.gov.tw dataset 11396, ODGL 1.0. Its endpoint is
`https://www.tpex.org.tw/openapi/v1/tpex_disposal_information`; the route is
`eligible` and `runtime_executable=false`. The descriptor, A2.2 readiness
record, and A2.3 source-authority mapping agree. No activation was performed.

The existing `normalize_tpex_disposition` requires `Date`,
`SecuritiesCompanyCode`, `CompanyName`, `DispositionPeriod`,
`DispositionReasons`, and `DisposalCondition`; it emits H1 v1 subtype
`disposition`. Its `_date_value` accepts only calendar-valid `YYYY-MM-DD`.
Its `_bound_row` accepts zero or one exact string-code match and fails when
more than one row matches.

## One bounded acquisition

- Requested/effective URL: `https://www.tpex.org.tw/openapi/v1/tpex_disposal_information`
- GET attempts: 1; HEAD/POST/retry/fallback: 0/0/0/0
- HTTP 200, `application/json`, Content-Length and response bytes: 25,231
- Response SHA-256: `387fc06c42a3fabcd4dc81308c690d438044bb21e9434d67efa135a39e105864`
- Retrieved: `2026-10-07T05:40:21.117382Z`
- TLS: repository `compatibility` policy; `CERT_REQUIRED` and hostname checking
  remained enabled; `VERIFY_X509_STRICT` was available and removed as governed.
- Timeout 30 seconds; maximum response 4 MiB; redirects rejected; observed
  redirects 0. No configured urllib proxy or proxy/CA environment overrides.
- Payload was decoded strictly as UTF-8, analyzed in memory, and not persisted.

## Observed live contract

The response was a non-empty JSON array of 26 objects. Key union and
intersection both contain exactly the six expected fields. Each required key
was present on all 26 rows; no unexpected fields occurred. Each required field
was a JSON string in all rows, with zero blank, null, or missing values.

| Field | Observed type | Blank / null / missing |
| --- | --- | --- |
| `Date` | string: 26 | 0 / 0 / 0 |
| `SecuritiesCompanyCode` | string: 26 | 0 / 0 / 0 |
| `CompanyName` | string: 26 | 0 / 0 / 0 |
| `DispositionPeriod` | string: 26 | 0 / 0 / 0 |
| `DispositionReasons` | string: 26 | 0 / 0 / 0 |
| `DisposalCondition` | string: 26 | 0 / 0 / 0 |

Every `Date` was a seven-digit string; there were seven distinct nonblank date
tokens. The dormant parser accepted 0/26. No ROC/Gregorian conversion was
performed. The parser's calendar validity for this seven-digit grammar remains
unresolved, and the current dormant normalizer therefore cannot provide a
deterministic source snapshot or target record date.

`SecuritiesCompanyCode` was a numeric string on all 26 rows. Lengths were 4
(12 rows), 5 (12), and 6 (2); no leading-zero codes were observed. There were
20 unique nonblank strings, 4 duplicated code values, and a maximum of 3 rows
for one code. The source identifier must remain a string. The dormant
normalizer's one-row binding assumption is not compatible with every observed
target cardinality; no row was discarded and no “latest” row was selected.

## Offline normalizer check and semantics

Using the in-memory response only, the deterministic sample target was selected
by the lexicographically smallest unique nonblank `SecuritiesCompanyCode`.
The dormant normalizer emitted a schema-valid and semantically valid H1 v1
artifact with one `disposition` item and only `disposition` coverage. However,
both the source snapshot date and selected item's source record date were null
under the current date parser. The test does not make the live contract
compatible; duplicate-code targets can also fail with
`binding_failed:ambiguous_exact_target_rows`.

The source-native fields support retaining the official date token, exact
security-code string, company name as provenance/display, disposition period,
reasons, and condition. They do not establish `effective_from`, `effective_to`,
ended/current lifecycle, same-day state, tradeability, or normal trading. A
missing target row remains partial source-specific evidence, not normal
trading or complete `no_evidence_in_covered_scope`. A2.3's source authority
allows this component to contribute `disposition` only.

## Evidence matrix

| Gate | Result |
| --- | --- |
| Authority identity | PASS |
| Dataset/license mapping | PASS |
| Official endpoint identity | PASS |
| Transport | PASS |
| Top-level JSON shape | PASS |
| Required fields | PASS |
| Field types | PASS |
| Date grammar against current parser | FAIL |
| Identifier grammar as exact strings | PASS |
| Identifier uniqueness/cardinality | FAIL |
| Dormant normalizer overall live compatibility | FAIL |
| H1 v1 projection for deterministic unique sample | PASS; dates remain null/unresolved |
| Source-specific canonical coverage | PASS; disposition only |
| Lifecycle semantics | PARTIAL / UNRESOLVED |

## Decision and next gate

The initial A2.4 hard date and exact-target cardinality gates failed. The
historical initial result remains
`J_B03_A2_4_HOLD_LIVE_SOURCE_CONTRACT_INCOMPATIBLE`; it is not rewritten by
later work. Under the continuation authorization, R1 repaired only the dormant
TPEx disposition normalizer and passed offline validation. R2 fresh live
re-verification is pending, so this record does not yet claim final source
contract verification.

H1 v1, H1 v2, Composite v1, Result V3, OperationResult v2, and the H0-G
manifest retain their required hashes. No production/schema/catalog/routing/
registry/activation/preferred-version/MCP changes occurred. MCP remains 6.
Market GET/HEAD/POST = 1/0/0. `data/` was untouched; no payload was committed.
H0-SRC-01E and H0-SRC-02 remain OPEN; J-B03 remains HOLD; J-B04 remains
BLOCKING; Phase J remains NOT STARTED.

## A2.4-R1 — Offline normalizer repair

**Authority:** `USER_CHAT_2026-10-07_J_B03_A2_4_R1_R2_CONTINUATION_AUTHORIZATION`

R1 preserved the original A2.4 HOLD and added a TPEx disposition-specific
date path. Canonical ISO dates are calendar-validated; seven ASCII digits are
parsed only through the existing `parse_roc_yyyymmdd()` precedent. Invalid ROC
calendar dates fail closed. The raw date token remains in each complete
source-native row provenance, while `source_record_date` carries the normalized
Gregorian date. A table snapshot date is emitted only when every row resolves
to the same date; mixed normalized dates leave it null with a caveat.

Disposition binding now requires a non-empty string target code and exact
string equality. It preserves every matching source row as a separate
`disposition` / `reported` item, including two or three rows for one code. It
does not select or deduplicate rows, infer a latest record, or assign effective
dates. Generic `_bound_row()` and generic `_date_value()` were not broadened.
Required source fields must be strings; blank free-text values are retained.
No-match remains a partial source-specific result and does not mean normal
trading.

R1 offline tests: **56 passed, 0 failed** across disposition normalizer and
composition suites, including R1-C1 through R1-C12. The Phase H V3 validator,
`compileall scripts server tests`, and `git diff --check` passed. R1 market
GET/HEAD/POST was **0/0/0**. No schema or runtime activation changes were made.

## A2.4-R2 — Fresh live re-verification

Status: **PENDING**. No R2 request has been made yet. After the R1 repair
commit, R2 may use the separately authorized bounded official endpoint and
must record its own request accounting and response evidence. Final A2.4
disposition remains pending R2.

## Verification history

1. Initial A2.4 live probe: `HOLD_LIVE_SOURCE_CONTRACT_INCOMPATIBLE` (one GET).
2. R1 offline repair: PASS (zero market requests).
3. R2 live re-verification: pending.

The six protected H1/Composite/Result/OperationResult/H0-G hashes remain
unchanged. MCP remains exactly 6; the source remains `eligible` and
`runtime_executable=false`; `data/` remains untouched and the raw source
payload is not committed.
