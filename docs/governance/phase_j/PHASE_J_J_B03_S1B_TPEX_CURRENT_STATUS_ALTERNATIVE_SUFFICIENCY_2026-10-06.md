# J-B03-S1B — TPEx Current Trading-Status Alternative

**Disposition:** `J_B03_S1B_ALTERNATIVE_CURRENT_STATUS_SEMANTICALLY_SUFFICIENT`

## Finding

Official metadata supports a narrow present-status use for `H1-TPEX-CHANGED-TRADING-OPENAPI` (`/openapi/v1/tpex_cmode`). Data.gov.tw [dataset 11736](https://data.gov.tw/dataset/11736) names the dataset **上櫃股票變更交易、分盤交易、管理股票與停止交易資訊**, lists a source-native `停止交易` field, reports daily updates, and applies ODGL 1.0. TPEx's [official query page](https://www.tpex.org.tw/zh-tw/mainboard/trading/info/altered.html) offers a query by data date for that same named status information. Current repository authority maps dataset 11736 to `/tpex_cmode` and records daily current-status snapshot coverage.

The coverage is a **special-status list**, not a proven all-security snapshot with explicit positive and negative flags. A current-date row with exact target binding and a subsequently verified affirmative stop value can support the bounded statement that TPEx reports the security stopped from trading. A row with a negative or blank value does not establish that it is not stopped. An absent row does not mean normal trading. The API schema was not available through the research path (TPEx OpenAPI docs returned 403); the source-value encoding and exact English-to-Chinese field mapping remain for a separately authorized shape/contract gate.

Semantic classification: `SUPPORTED_BUT_SCOPE_LIMITED`.

## Conversational use

- **「這檔現在是不是停止交易？」** Answer yes only with a current-date, exact-target row and a source-verified affirmative `停止交易` value; otherwise say unresolved. Absence is not a no.
- **「這檔今天為什麼不能正常交易？」** Disposition conditions and stopped-trading status are separate evidence. If neither explains the case, report insufficient evidence rather than infer a cause.
- **「它以前有沒有停牌或恢復交易？」** The history route may provide bounded official event rows; it does not prove current state or complete lifecycle.
- **「它今天幾點恢復交易？」** This alternative does not establish exact event timing. Return unsupported/unresolved unless a separately verified source supports it.

Accordingly, unresolved `tpex_spendi_today` event detail is `OPTIONAL_CURRENT_EVENT_DETAIL_NOT_J_B03_BLOCKING` for the representative conversational slice. This does not resolve that source's contract issue, close H0-SRC-01E, or authorize route implementation or activation.

## Issue and execution boundaries

- `H0-SRC-01E` remains OPEN; `H0-SRC-02` remains OPEN for full-H1 lifecycle/completeness.
- Market-data GET/HEAD/POST = 0. No market payload was requested.
- No production, schema, catalog, routing, executor registry, activation, or MCP change. MCP remains 6.
- J-B03 remains HOLD; J-B04 remains BLOCKING; Phase J remains NOT STARTED.
- The next gate is a separate authorization for `J-B03-S2B` one-shot source-shape verification. No such GET is performed here.

See the adjacent JSON record for the exact metadata inventory and evidence limits.
