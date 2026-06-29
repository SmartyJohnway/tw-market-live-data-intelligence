# M5K TAIFEX TX futures preflight

## Scope

This is a design/research preflight only. M5K execution remains fail-closed for `TX` / TAIFEX futures until a quote endpoint, contract-month selector, and timestamp semantics are verified with reproducible evidence.

## Endpoints and sources investigated

| Source | Type | Endpoint / page | Method | Finding |
|---|---|---|---|---|
| TAIFEX product specification | Official exchange page | `https://www.taifex.com.tw/enl/eng2/tX` | Browser/document read | Confirms English code `TX`, ticker symbol `TXF`, delivery months, and last trading day semantics. |
| TAIFEX market quotes navigation | Official exchange site | `https://www.taifex.com.tw/enl/eIndex` | Browser/document read | Indicates TAIFEX publishes market quote pages, but this preflight did not verify a stable JSON API contract for M5K. |
| Government data standard | Official/semi-official schema reference | `https://schema.gov.tw/lists/74` | Browser/document read | Defines futures quote fields including contract month/week format; useful for normalization, not itself a live quote endpoint. |

## Contract-month semantics

`TX` alone is ambiguous for live observation. It can mean at least:

1. nearest listed month / spot month,
2. a specific contract month such as `TXF202607`,
3. continuous front-month series,
4. a user-selected contract from all listed months.

Official contract specifications list the spot month, the next two calendar months, and the next three quarterly months. The last trading day is the third Wednesday of the delivery month. Because rollover can change the meaning of "front month," M5K must not silently map `台指期` or `TX` to a contract without exposing the selected contract month and rollover rule.

## Reliability and update frequency assessment

No production M5K TX quote execution was added. The official product page is reliable for product semantics, but it is not a machine-verified current quote endpoint. Market quote pages may be browser-rendered and require separate low-frequency endpoint discovery before use. Update frequency was not verified in code.

## Required parameters for a future implementation

A safe future M5K contract should require:

- `symbol`: `TX` or `TXF`,
- `market`: `taifex`,
- `instrument_type`: `futures`,
- `contract_selector`: one of `specific_contract`, `front_month`, or `manual`,
- `contract_month`: required when `contract_selector=specific_contract`, using a documented format such as `YYYYMM`,
- explicit source timestamp and retrieval timestamp,
- explicit delay status and realtime disclaimer.

## Sample response

No live TAIFEX quote endpoint sample is committed in this PR. The live research in this PR was limited to low-frequency official documentation lookup, not quote probing. Therefore, there is no verified response body to parse.

## Risks

- Ambiguous symbol mapping can misrepresent the observed contract.
- Rollover rules can change observed values without user awareness.
- Browser quote pages may not be a stable public API.
- Commercial or broker APIs may require credentials and must not be embedded in this repository.
- A delayed quote must not be labelled realtime unless the source explicitly proves realtime status.

## Recommendation for next implementation step

Keep automatic TX routing disabled in M5K. The next PR should perform a separate low-frequency TAIFEX endpoint probe with exact URL, headers, status code, response sample, parsed fields, source timestamp, retrieval timestamp, and legal/maintenance risk. Only after this evidence exists should M5K add a `taifex_tx_quote` adapter, and it should require a user-visible contract selector rather than treating `TX` as an implicit continuous or front-month symbol.

## Current M5K status

- implemented execution: false
- kept fail-closed: true
- status: `unsupported_in_m5k_initial`
