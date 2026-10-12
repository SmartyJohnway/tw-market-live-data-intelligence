# J-B04-A6-SM-B1-R5-P2 — TWSE Lifecycle Redirect Contract Qualification

**Disposition:** `SM_B1_R5_P2_TWSE_LIFECYCLE_CONTRACTS_PARTIAL`

The authorized baseline was `b05ae6dc548e305ae4783420b46ae0eb6b743f41`, tree `1103202d7f90494e6a0339467a01e3257f52cb1b`, with `origin/main` at `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. Prior R5-P1-R2-R1 review: `5478405866`. Owner authorization SHA-256: `002d84ae99ba9ed6de4c8d517985804848c768d8a7da35c52e1b666716284af1`.

## Probe accounting

Six logical GET probes caused six explicit HTTP dispatches: one for `twse_delisted` and five for `twse_etn_expired`. There were zero redirects followed, zero retries, zero HEAD/POST requests, and no browser traffic. The temporary runner’s local pre-dispatch self-test rejected all six invalid method tokens (`landing`, `probe`, `FETCH`, `get`, empty string, and null) before dispatch.

No TPEx request, Security Master acquisition/bootstrap, H3/H2 live execution, or A6 integrated execution occurred. Network activity stopped after the ETN JSON response was captured.

## TWSE delisted

The historical materializer URL, `https://www.twse.com.tw/company/suspendListingCsvAndHtml?lang=zh&type=html`, now returned HTTP 200 directly. It did not redirect. The 51,814-byte response was HTML with one table and 265 lifecycle rows. The headers were `終止上市日期`, `公司名稱`, and `上市編號`.

The existing `parse_twse_delisted` adapter parsed all 265 rows. Parsed dates span `2001-01-20` through `2026-09-01`; dates use the ROC/Minguo calendar and were normalized by the existing parser. There were no duplicate `(security_code, effective_date, event_type)` identities. No pagination controls or page metadata appeared in the returned response, so the one response contains the complete table offered by this source. The parser and production URL remain compatible; production acquisition requires one GET dispatch. This source is `QUALIFIED_DIRECT_CANONICAL_SOURCE` for the source-provided table.

## TWSE expired ETN

The historical URL, `https://www.twse.com.tw/zh/products/securities/etn/products/expire.html`, returned HTTP 200 without a redirect, but the response was a client-loaded shell with no HTML table. Its form exposed `data-api="/ETN/expireEnd"`. The page referenced first-party `main.js` and `web-report.js` assets. Static inspection showed the production runtime composes the `/rwd/zh` base and the report code uses `$.getJSON`, adding `response=json` and optional page-provided arguments.

The directly composed read-only request `https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json` returned HTTP 200 and JSON with root keys `stat`, `title`, `data`, and `fields`; `stat` was `ok`. The five fields were `終止上市日期`, `證券代號`, `證券簡稱`, `發行證券商`, and `終止上市理由`. It contained 13 rows dated from `2020-04-30` through `2026-05-28`. The existing ETN parser rejected this JSON as `no_html_tables`, which is fail-closed behavior.

The response has no total count or pagination marker. The initial page body was overwritten in temporary storage by a filename collision after its size, hash, and structural observations had been recorded. Consequently, the page’s on-load filter arguments and any paging attributes were not preserved for review. Coverage, full default request semantics, and parser compatibility are therefore not qualified. This source is `SOURCE_CONTRACT_PARTIAL`; do not promote it to production acquisition.

## Bootstrap fit and state

The qualified delisted source needs one deliberate GET. The previously qualified TPEx source needs one deliberate POST. The ETN source still blocks bootstrap readiness because completeness and its production parser contract are unresolved. The existing bootstrap envelope remains unchanged: five logical source probes, at most one followed redirect and two dispatches per probe, ten dispatches total, and zero retries.

Security Master remains `NOT_INITIALIZED`; `active.json` is absent and production identity is not verified. Bootstrap attempt #2 remains `NOT_AUTHORIZED`. H2 remains inactive and `plan_only`, selected executor is null, J-B04 remains blocking, Phase J remains not started, MCP remains six tools, and PR #326 remains Draft/open/unmerged.

The historical SM-B1 HTTP 307 observations remain accurate for that earlier execution. Both URLs returned HTTP 200 during this tranche without redirects. No production files were changed.

Detailed machine-readable telemetry, body hashes, parser results, and evidence-retention limitations are in the adjacent JSON record. Raw source payloads and JavaScript were not committed.
