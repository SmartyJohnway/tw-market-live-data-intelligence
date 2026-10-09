# J-B04-A5 bounded-live preflight — P0-R2

Disposition: `J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW`.

## Environment and identity assurance

The execution environment class is explicitly `cloud_clean_source_acceptance`. The production Mode A loader was consulted normally and reports the installation-local Security Master as `NOT_INITIALIZED`. No Security Master bootstrap or migration was run.

For this A5 source gate only, the frozen descriptor is `{"canonical_target_id":"TWSE:2330","market":"TWSE","security_code":"2330"}` with SHA-256 `d80f5c697d333f043df922a099a0f472780051c1d2abf79866954026b63aaa40`. It authorizes only exact `TWT48U_ALL` `Code` field binding. It does not establish current listing membership, ISIN, instrument family or type, lifecycle, or production execution eligibility.

`identity_assurance_level` is `acceptance_only_predeclared_source_target`; `production_identity_verified` is false; `A6_identity_reverification_required` is true. A6 still requires an ACTIVE / QUALIFIED canonical Security Master and exact production identity resolution. A5 evidence cannot waive that requirement.

## Source containment

The only planned source call remains one GET to `https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL`, with at most one actual HTTP dispatch, zero retries, redirects rejected, a 15-second timeout ceiling, and a 4 MiB response ceiling. H3, TWT49U, TPEx, browser fallback, and Security Master live acquisition are prohibited. Raw payload persistence is `NONE`.

The secondary lifecycle witness may use only the captured payload. It prefers a valid normalizable primary `TWSE:2330` row; if absent, it selects the lexicographically smallest `(Code, Date, canonical raw-row SHA-256)` among rows the unchanged normalizer can safely normalize. It proves only source-stage behavior; product-scope identity is unverified.

## History

- Initial P0 `7dd04753dbcd0ac39aac9229b3329d32f2e18478` stopped on an obsolete Candidate-B artifact prerequisite.
- P0-R1 `b5b0a03abd35800ba82070d7a484ee80819c620b` correctly diagnosed the canonical installation-local Security Master as `NOT_INITIALIZED`.
- P0-R2 refines the gate scope for an explicitly declared clean cloud source-acceptance environment. It does not change or dispute R1’s runtime finding.

No Owner A5 live authorization is present or requested at P0-R2. No TWT48U request has been made. H2 remains `INACTIVE`, selected H2 executor remains `null`, J-B04 remains `BLOCKING`, Phase J remains `NOT_STARTED`, and MCP remains 6.
