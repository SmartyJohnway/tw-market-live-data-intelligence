# J-B04-A6-SM-B1-R5-P1-R1 — TPEx Lifecycle Contract Qualification Restart

**Disposition:** `SM_B1_R5_P1_R1_TPEX_LIFECYCLE_CONTRACT_PARTIAL`

The current official TPEx page and its first-party JavaScript independently establish the lifecycle endpoint composition. Three bounded read-only POST probes confirmed the endpoint returns JSON. The source is not production-qualified because “all years” contains 582 rows but the current page requests ten per page, the tested zero-size request returned one row, and complete enumeration under the existing Security Master bootstrap dispatch budget is not established.

## Authority and prior incident

The authorized revision was HEAD `c09f6fda9fbebd39df982970342aeee70bd4873c`, TREE `38f637981e6a5facd2720103874d306163fd97ff`, with `origin/main` `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. Owner statement SHA-256: `08aadd17d403b461a955fa29fae3109da23e61e939a1edbd0aba51c243d80871`.

The prior R5-P1 HARD_BLOCK remains immutable, independently reviewed incident evidence (review `5477763503`). It was a temporary runner argument-order defect: `landing` reached the HTTP-method slot, one invalid method dispatch was attempted, and no response or valid TPEx request resulted. R1 replaced that interface with a keyword-separated temporary runner and a pre-dispatch guard. Its no-network self-test rejected `landing`, `probe`, `FETCH`, lowercase `get`, empty, and null methods; GET and POST were accepted; labels remained separate; outbound dispatch count was zero. The runner is external at `/tmp/j-b04-a6-sm-b1-r5-p1-r1/runner.py` (SHA-256 `de85cbd1bb4b8fb7d68fb09c6ac08ec023acb8446443d30debe6b6a1bceadaab`).

## Independently reproduced request chain

The current landing page declares `lang="zh-Hant-tw"`, loads `/rsrc/js/main.js` before `/rsrc/js/tables.js`, then calls `tables.init` with `pattern: API_PATTERN` and `action: "company/deListed"`. The captured `main.js` declares a top-level lexical `let API_PATTERN="/www/{LANG}/{ACTION}"`; this is compatible with a bare `API_PATTERN` binding while `window.API_PATTERN` is undefined. `tables.js` maps a Chinese document language to `zh`, then to `zh-tw`, and substitutes the first `{LANG}` and `{ACTION}` tokens. The resulting endpoint is:

`https://www.tpex.org.tw/www/zh-tw/company/deListed`

The landing config sets `autoLoad=true`, `serverPaging=true`, and `pagin=10`. `tables.js` posts the serialized form with `response=json`, then adds `paging-offset=0` and `paging-size=10`. Page navigation posts the selected page size, offset `(page-1)*size`, table index, and deterministic order fields.

## Probe results

Six logical probes used six dispatches: three GETs (landing, `main.js`, `tables.js`) and three POSTs to the lifecycle endpoint. No redirects, retries, browser traffic, credentials, or state-changing operations occurred.

| Purpose | Result | Bytes | SHA-256 |
|---|---|---:|---|
| Current landing | HTTP 200, `text/html` | 11,160 | `1b2d900b7727597d0e65c472546b2b896670622dd18cd1314c1e1da8638809a1` |
| `main.js` | HTTP 200, `application/javascript` | 45,227 | `cfbd8c64c748149f039f1d4f1c5b3ba4511039b9c9e60d8ed53fd9624edc587a` |
| `tables.js` | HTTP 200, `application/javascript` | 168,139 | `085fd65b4e15e2af4f3adb3f256f0058d0176dd2d98ce53217ede16667a04a90` |
| Default-page POST | HTTP 200, JSON; 6 current-year rows | 1,332 | `86b5cf847348056b6220d293b6a569e897939b57b6c3fc9ea5b5d1b6293036a2` |
| `date=ALL`, size 10 | HTTP 200, JSON; 10 of 582 rows | 2,065 | `80c6dc6d5c037f6db046ba36dee1754530edf2f5ba97ac3b5887d28817d25eb9` |
| `date=ALL`, size 0 | HTTP 200, JSON; 1 of 582 rows | 404 | `cacad15d3279efcd281031c2c71c931c0d89c2bf96335541fb94ad4fae1dc2e6` |

Default form values included blank `code`, blank `date`, and `reason=-1` (“all”); the server response reported `date=2026`. `date=ALL` is supported by the page’s `YA` date selector. The response uses root keys `tables`, `date`, `stat`; `tables[0]` contains `fields`, array-of-array `data`, `totalCount`, `title`, and `notes`. Observed field order is stock code, company name, termination date, termination reason, company-data URL. The observed row maps code `8183`, a company name, ROC-shaped date `115-10-01`, and a non-empty reason. The repository lifecycle contract treats this date form as ROC and converts the year by adding 1911, giving `2026-10-01` while retaining the raw value.

## Qualification gap

The endpoint, method, form encoding, language/action composition, response root and core row fields are established. Complete production coverage is not. The official client is configured for ten rows per server page. `date=ALL` reports 582 rows, while the experiment with `paging-size=0` returns only one row, not all 582. The client exposes offsets but the next page, duplicate/missing-page detection, maximum accepted page size, oldest history, empty-result behavior, error responses, and full filter semantics were not qualified. About 59 ten-row pages would exceed the existing five-source/ten-dispatch Security Master bootstrap envelope. No production source manifest, parser, or materializer was changed.

The prior TWSE delisted and TWSE ETN HTTP 307 incidents remain separate known blockers. If reproduced, the current materializer records those as acquisition failures. R1 did not retest them.

## Terminal boundaries

Security Master remains `NOT_INITIALIZED`; production identity is unverified; bootstrap attempt #2 is `NOT_AUTHORIZED`. H2 remains inactive and `plan_only`; selected executor is null; J-B04 remains blocking; Phase J is not started; MCP count remains 6. No bootstrap, H3/H2/A6 execution, H2 activation, or merge occurred. PR #326 remains Draft, open, and unmerged.

Raw response bodies and JavaScript remain under `/tmp/j-b04-a6-sm-b1-r5-p1-r1/` and are not committed. The R5-P1 historical JSON/Markdown evidence is byte-identical to its recorded hashes.
