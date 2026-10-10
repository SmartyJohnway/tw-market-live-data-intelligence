# J-B04-A6-SM-B1-R5-P2-R1 — TWSE ETN evidence and coverage qualification

**Disposition:** `SM_B1_R5_P2_R1_TWSE_ETN_CONTRACT_QUALIFIED_BOOTSTRAP_FIT`

This gate repaired the overwritten-evidence gap with a fresh, collision-free capture and qualified the exact page-generated ETN request. It did not run the Security Master bootstrap or any other market execution.

## Authority and scope

The authorized starting point was HEAD `d411933247487075e250f41db87688fe02fa5740`, tree `acb77b24a32677279fff7a16869231899fb25747`, with `origin/main` `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. R5-P2 review `5478481588` accepted `twse_delisted` and left only `twse_etn_expired` partial. The Owner authorization statement hash is `5467ebfa813bae9ddea8a4b1e501c5c70d5423b30b206f6d7e1a7b6d137bd32d`.

Only `twse_etn_expired` was probed. There were two logical GETs and two HTTP dispatches: one fresh landing capture and one page-derived JSON request. No redirects, retries, browser traffic, TPEx requests, `twse_delisted` requests, HEAD/POST, or Security Master acquisition occurred. The source network was frozen after the second response.

## Preserved landing and request contract

The fresh landing response was HTTP 200 with no redirect, `text/html`, 11,284 bytes, SHA-256 `265d3eeb30e292795ad9a089f6e34f10c6c5b781b756c9766f796717b97cb8d9`. This exactly matches the historical R5-P2 byte count and hash; the R5-P2 overwritten-file limitation remains true for that earlier run.

The page has one form (`id=form`) with `data-api=/ETN/expireEnd`, no explicit action or method, no form controls or hidden inputs, no report filters, and no `onload-argv`. The only page controls outside the form are presentation/navigation controls. The report table has neither `data-paging` nor `data-server-side`. Preserved first-party runtime captures show the report derives `/rwd/zh` from the configured RWD base and page language, calls `getJSON` once, adds `response=json`, and renders the returned data array client-side. There is no subsequent page/offset request. Runtime asset captures were reused locally and not fetched again.

The exact page-generated data request is one GET to `https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json`, with only `response=json`; blank controls and filters are absent, and no paging parameters are sent. The fresh JSON response was HTTP 200, `application/json;charset=UTF-8`, 1,703 bytes, SHA-256 `e049ed302b3bdd7b73bc77a3c8d2d015835da6882db8652f397d4c8514019484`.

## Qualified data and completeness contract

The response has the exact root keys `stat`, `title`, `data`, and `fields`; `stat` is `ok`; title is `到期或終止上市資訊`; and fields are exactly, in order: `終止上市日期`, `證券代號`, `證券簡稱`, `發行證券商`, `終止上市理由`. All 13 rows are five-string arrays aligned to that field order. Codes, names, issuers, reasons, and dates are present. The dates use Gregorian `YYYY/MM/DD`, normalize to ISO dates, and span 2020-04-30 through 2026-05-28. There are no duplicate complete rows or duplicate `(security_code, effective_date)` lifecycle identities.

The page exposes no year/date/status/code/reason filters, hidden defaults, onload arguments, server paging, or client page-size configuration. Its runtime makes one GET and renders the response array without another page request. Therefore the 13 rows are qualified as the complete dataset offered by this report at acquisition time. No `totalCount` is provided; this qualification does not claim events outside the exchange's offered dataset. A valid empty result is accepted only with the exact success/root/title/field contract and `data=[]`. Non-`ok`, malformed, or structurally invalid payloads remain schema drift, never empty data.

The parser emits `twse_delisted` from the explicit termination date. The source has no separate maturity or last-trading date fields; neither is inferred from free-text reason text.

## Production repair and validation

Implementation commit: `eba68f0c0f37c56c1aad6e60da1f0f557f414773` (tree `c3629c3ecf5b26829b7f7e7bc7f3c914b889ea1f`). The production path now uses the direct JSON GET and a separate strict JSON adapter; transport failure hard-stops before Phase E/export/activation, while schema drift retains its separate classification. The existing HTML parser remains available for legacy supplied captures. The manifest and lifecycle contract describe the JSON source and page-derived completeness basis. Historical validators now read their contemporaneous manifest snapshots and recognize this explicitly bounded supersession.

The preserved fresh JSON response replays to 13 lifecycle events, all valid against the repository LifecycleEvent schema, with zero duplicate identities. Focused tests passed 101/101. Clean-archive default-CI ran under CPython 3.12.14 and a local network-deny guard: both base and candidate collected 1,288, selected 1,283, passed 1,234, failed the same 45 nodes, skipped 4, and deselected 5. New failure delta is zero. Compileall, source-manifest schema validation, the relevant historical validators, and `git diff --check` passed.

## Bootstrap fit and state

The five-source bootstrap remains unchanged: two identity GETs, TWSE delisted, TPEx delisted, and TWSE ETN expired. Normal no-redirect use is five dispatches; the existing ceiling remains at most two per probe and ten total, with no automatic retries. This ETN source requires one deliberate GET and fits the existing envelope.

The Security Master remains `NOT_INITIALIZED`; no active selector/release or production identity was created. Bootstrap attempt #2 remains `NOT_AUTHORIZED`. H2 remains inactive and plan-only, selected executor is null, J-B04 remains blocking, Phase J remains not started, and MCP remains six tools. PR #326 remains Draft/open/unmerged.

Complete local raw artifacts and their hashes are recorded in the accompanying JSON and `/tmp/j-b04-a6-sm-b1-r5-p2-r1/final-hash-manifest.json`. The response bodies and Owner authorization record were not committed. R5-P2 evidence was not changed.
