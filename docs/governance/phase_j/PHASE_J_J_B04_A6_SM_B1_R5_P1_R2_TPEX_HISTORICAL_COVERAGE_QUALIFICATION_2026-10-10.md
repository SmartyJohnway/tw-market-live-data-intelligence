# J-B04-A6-SM-B1-R5-P1-R2 — TPEx historical coverage and pagination qualification

**Disposition:** `SM_B1_R5_P1_R2_TPEX_HISTORICAL_COVERAGE_QUALIFIED_BOOTSTRAP_FIT`

The current official TPEx company-delisting endpoint returned its entire `date=ALL` result in one response at `paging-size=1000`. The response contained 582 rows and declared `totalCount=582`; every row matched the five-field schema, all ROC dates parsed, and no duplicate lifecycle identities were found. This satisfies the deterministic, single-dispatch acquisition needed by the current Security Master bootstrap envelope.

This qualification covers the history represented by the endpoint’s `ALL` result: 582 rows spanning 1992-10-27 through 2026-10-01. It does not claim events beyond the endpoint’s available history. The response had no snapshot marker; the one-response design avoids cross-page mutation and reconciliation risk. The service’s maximum possible page size was not mathematically probed because 1000 was sufficient for the complete observed result.

## Authority and probe accounting

The tranche began at HEAD `05583ea56b5bfe79d81a6f1b2686c63ce3fa06ef`, TREE `b4c6a94ceb68ec1e5228e730eda16bbca35acd10`, with `origin/main` `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. R5-P1-R1 review `5478113925` had accepted endpoint discovery and left historical coverage partial. This tranche’s Owner statement hash is `e7b57d5550a897417d79b5cc78d7e4c530ccc834dc65a552c457b33225d4a5e0`.

Four logical POST probes consumed four HTTP dispatches. There were no retries, followed redirects, GETs, HEADs, browser incidental requests, or endpoint rediscovery. The sequence was:

1. `date=ALL`, `reason=-1`, empty code, offset 0, size 1000: HTTP 200, `stat=ok`, 582 rows, `totalCount=582`, 71,065 bytes, SHA-256 `d70bcef49999ffb4c6642ae1e55910e26636d02fd4eb90f8eab84094b98de4a5`.
2. Valid nonexistent code `0000`: HTTP 200, `stat=ok`, empty `data`, `totalCount=0`, 190 bytes, SHA-256 `790cca17695523462f489e7d8934500e4379946270694ab258a5cb24bfba3d75`.
3. Malformed reason: HTTP 200 and the same 582-row result; the provider ignored the invalid reason. The production request therefore freezes `reason=-1`.
4. Malformed date: HTTP 200 JSON application error with non-`ok` status, 29 bytes, SHA-256 `1e8b8f9407c7e6ee97fe994fb9be3f2389383678c42cd455435706d373476954`. This distinguishes a source error from a valid empty response.

R1’s earlier observations remain historical evidence: size 10 returned 10 of 582 rows; size 0 returned one row, so size 0 does not mean “all.” The R2 size 1000 returned all 582 rows. No page 2 or final-page probe was needed; production does not paginate.

## Qualified request and response

The landing interface is `https://www.tpex.org.tw/zh-tw/mainboard/listed/delisted.html`. Its client contract composes `API_PATTERN=/www/{LANG}/{ACTION}`, maps `zh-Hant-tw` to `zh-tw`, and supplies action `company/deListed`, producing `https://www.tpex.org.tw/www/zh-tw/company/deListed`.

The production request is one HTTPS POST with `Content-Type: application/x-www-form-urlencoded; charset=UTF-8` and fixed parameters:

```text
code=
date=ALL
reason=-1
response=json
paging-offset=0
paging-size=1000
```

The response is `application/json;charset=UTF-8`. It has root keys `tables`, `date`, and `stat`; successful `stat` is `ok`, `date` is `ALL`, and the one table contains `fields`, `data`, `totalCount`, `title`, and `notes`. The ordered fields are stock code, company name, termination date, termination reason, and company data URL. Each data row is a five-string positional array. Production requires exact field order, required code/name/date values, and `len(data) == totalCount <= 1000`.

All 582 termination dates were valid ROC dates. The existing date normalizer applies Gregorian year = ROC year + 1911 and retains the raw date. Blank reason values occur in 293 rows; they remain blank/unknown rather than being inferred. Duplicate `(security_code, effective_date)` identities: 0. The first and last bounded observations were codes 8183 / 2108 at raw dates 115-10-01 / 81-10-27.

## Production repair

Implementation commit `47e9c1ab997ce6bc2bfff37bc84344957da7daa7` (TREE `9f80b61d1b53d4c812fd81ce996823ed9314f78b`) promotes the manifest to the qualified JSON endpoint, documents the data contract, uses the fixed POST in the existing materializer, and adds the JSON adapter while retaining legacy supplied-HTML fixture support. The parser fails closed on malformed JSON, non-`ok` application status, schema or row-count drift, invalid/non-ROC dates, missing required values, duplicate lifecycle identities, and responses above the qualified 1000-row bound. TPEx transport or parser failure stops before another logical probe, Phase E qualification, export, candidate construction, or activation. Raw response capture remains installation-local.

The existing transport contract remains unchanged: five logical source probes, at most one followed redirect and two dispatches per probe, ten total dispatches, zero automatic retries. TPEx uses one deliberate source dispatch, so it fits. No bootstrap was executed and this qualification does not authorize bootstrap attempt #2.

## Validation and limitations

Compilation, the source-manifest schema check, manual offline parser/POST checks, strict duplicate-key JSON scan, `git diff --check`, and A6-P1, P1-R1, SM-B1-R2, SM-B1-R3, and A6-P0 validators passed. The production parser also replayed the preserved local 71,065-byte response and emitted 582 lifecycle events that all passed the LifecycleEvent schema.

Pytest was unavailable in the active Cloud Python (`No module named pytest`); offline installation confirmed no cached wheel, so no network was used to install it. The clean-archive `default-ci` comparison ran the same profile on baseline `05583ea56b5bfe79d81a6f1b2686c63ce3fa06ef` and candidate `47e9c1ab997ce6bc2bfff37bc84344957da7daa7`; both failed before collection for that same environment reason. Collected, selected, and deselected counts are unavailable; no tests were collected. This is not a CI pass.

R5-P1-R1 history is unchanged. Security Master remains `NOT_INITIALIZED`; production identity is not verified. Bootstrap attempt #2 remains `NOT_AUTHORIZED`. The prior TWSE `twse_delisted` and `twse_etn_expired` HTTP 307 incidents remain unresolved, so they are separate predicted blockers to a future bootstrap. H2 remains inactive and unselected; routing remains `plan_only`; J-B04 remains blocking; Phase J remains not started; MCP remains six tools. PR #326 remains Draft, open, and unmerged.

No TPEx raw response or full row set is committed. Sanitized probe metadata and raw response hashes/paths are recorded in the adjacent JSON record; the local captures remain under `/tmp/j-b04-a6-sm-b1-r5-p1-r2/`.
