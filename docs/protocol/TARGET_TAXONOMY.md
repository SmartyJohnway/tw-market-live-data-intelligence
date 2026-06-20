# Target Taxonomy

This document defines the canonical target classes for the Taiwan market intelligence project. It provides human-readable descriptions, examples, and capabilities to standardize how targets are described and categorized within the system.

## Canonical Target Classes

### `twse_common_stock`
* **Description:** Standard common equity shares listed on the primary Taiwan Stock Exchange.
* **Example Symbols:** 2330 (台積電), 1435 (中福)
* **Exchange / Venue:** TWSE (Taiwan Stock Exchange)
* **Equity-like:** Yes
* **EOD-reference compatible:** Yes
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Generally highly liquid and widely supported across official and unofficial sources.

### `tpex_common_stock`
* **Description:** Common equity shares listed on the Taipei Exchange (OTC market).
* **Example Symbols:** 8069 (元太), 5347 (世界)
* **Exchange / Venue:** TPEx (Taipei Exchange)
* **Equity-like:** Yes
* **EOD-reference compatible:** Yes
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** May exhibit lower liquidity than TWSE stocks; separate official EOD source required (TPEx OpenAPI vs TWSE OpenAPI).

### `twse_etf`
* **Description:** Exchange Traded Funds listed on the TWSE.
* **Example Symbols:** 0050 (元大台灣50 ETF), 00929 (復華台灣科技優息 ETF)
* **Exchange / Venue:** TWSE
* **Equity-like:** Yes
* **EOD-reference compatible:** Yes
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Often supported via the same endpoints as TWSE common stocks.

### `tpex_etf`
* **Description:** Exchange Traded Funds listed on the TPEx.
* **Example Symbols:** (e.g., 00888)
* **Exchange / Venue:** TPEx
* **Equity-like:** Yes
* **EOD-reference compatible:** Yes
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Similar to TPEx common stocks, requiring TPEx-specific endpoints for EOD data.

### `twse_tdr`
* **Description:** Taiwan Depositary Receipts. Foreign stocks trading on the TWSE in TWD.
* **Example Symbols:** 9105 (泰金寶-DR)
* **Exchange / Venue:** TWSE
* **Equity-like:** Yes
* **EOD-reference compatible:** Yes
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Thinly traded; can trigger edge cases or lack support in some third-party aggregators.

### `twse_index`
* **Description:** Market indices calculated and published by TWSE.
* **Example Symbols:** TAIEX (tse_t00.tw / ^TWII)
* **Exchange / Venue:** TWSE
* **Equity-like:** No
* **EOD-reference compatible:** Varies (often handled via separate index datasets rather than stock quotes).
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** No (cannot be traded directly).
* **Primary Caveats:** Typically only available as a benchmark or context point; no trading volume of its own.

### `tpex_index`
* **Description:** Market indices calculated and published by TPEx.
* **Example Symbols:** TPEx Index
* **Exchange / Venue:** TPEx
* **Equity-like:** No
* **EOD-reference compatible:** Varies.
* **Live-watchlist compatible:** Yes
* **Execution-capable through broker APIs:** No.
* **Primary Caveats:** Often requires specific index data channels distinct from equities.

### `taifex_index_future`
* **Description:** Futures contracts tracking indices, trading on TAIFEX.
* **Example Symbols:** TX (台指期)
* **Exchange / Venue:** TAIFEX (Taiwan Futures Exchange)
* **Equity-like:** No
* **EOD-reference compatible:** Varies (not supported by TWSE/TPEx OpenAPI).
* **Live-watchlist compatible:** Unconfirmed / Requires specialized sources.
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Expiration cycles, leverage, and separate exchange venue mean it is generally unsupported by stock-focused sources.

### `taifex_stock_future`
* **Description:** Single-stock futures contracts trading on TAIFEX.
* **Example Symbols:** (e.g., TSMC stock futures)
* **Exchange / Venue:** TAIFEX
* **Equity-like:** No (derivative)
* **EOD-reference compatible:** Varies.
* **Live-watchlist compatible:** Unconfirmed.
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Low liquidity on some contracts; distinct from the underlying equity.

### `mutual_fund`
* **Description:** Unlisted mutual funds (non-ETF).
* **Example Symbols:** FUNDA (placeholder)
* **Exchange / Venue:** N/A (purchased via distributors/brokers).
* **Equity-like:** No
* **EOD-reference compatible:** No (usually calculated via NAV once per day).
* **Live-watchlist compatible:** No.
* **Execution-capable through broker APIs:** Varies (often through specific wealth management APIs).
* **Primary Caveats:** Not traded intraday; standard quote sources (like Yahoo Finance) often fail or return placeholder errors.

### `foreign_stock_or_adr`
* **Description:** Equities or ADRs listed on foreign exchanges (e.g., US markets).
* **Example Symbols:** TSM (TSMC ADR)
* **Exchange / Venue:** Foreign (e.g., NYSE, NASDAQ)
* **Equity-like:** Yes
* **EOD-reference compatible:** N/A for Taiwan endpoints.
* **Live-watchlist compatible:** Yes (via global sources like Yahoo Finance).
* **Execution-capable through broker APIs:** Yes (sub-brokerage).
* **Primary Caveats:** Outside the scope of local TWSE/TPEx endpoints.

### `broker_account_target`
* **Description:** Internal representation of an asset held within a specific broker account for execution or portfolio tracking.
* **Example Symbols:** N/A
* **Exchange / Venue:** Broker-specific
* **Equity-like:** N/A
* **EOD-reference compatible:** N/A
* **Live-watchlist compatible:** N/A
* **Execution-capable through broker APIs:** Yes
* **Primary Caveats:** Highly sensitive; documentation only unless explicit credentials and scope exist.

### `unknown_or_unsupported`
* **Description:** Catch-all for assets that do not fit into the established taxonomy or for which source capability is entirely unknown.
* **Example Symbols:** Invalid symbols or unclassified instruments.
* **Exchange / Venue:** Unknown
* **Equity-like:** Unknown
* **EOD-reference compatible:** Unknown
* **Live-watchlist compatible:** Unknown
* **Execution-capable through broker APIs:** Unknown
* **Primary Caveats:** Used as a safe fallback for parser failures or ambiguous user inputs.
