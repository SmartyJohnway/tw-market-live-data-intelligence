# Source x Target Support Matrix

This matrix details the capability of various data sources to provide intelligence on specific Taiwan market target classes.

**Important Note:** The statuses used in this matrix adhere strictly to the definitions in `SUPPORT_STATUS_SEMANTICS.md`. `supported_observed` requires direct current repo evidence. If support is inferred from source scope or common market structure but not directly observed in this repository, use `supported_candidate`.

## Source Capabilities

### TWSE OpenAPI
*Official EOD/reference source for TWSE.*
* **TWSE common stock:** `supported_observed` (EOD data via STOCK_DAY_ALL, repo evidence exists).
* **TPEx common stock:** `unsupported` (Different exchange).
* **TWSE ETF:** `supported_candidate` (structurally plausible from source scope, but not directly observed by current repo evidence).
* **TPEx ETF:** `unsupported`.
* **TWSE TDR:** `supported_candidate` (structurally plausible from source scope, but not directly observed by current repo evidence).
* **TWSE index:** `unsupported` (Not supported by STOCK_DAY_ALL).
* **TPEx index:** `unsupported`.
* **TAIFEX futures:** `unsupported`.
* **Mutual fund:** `unsupported`.
* **Foreign stock/ADR:** `unsupported`.
* **Broker account target:** `unsupported`.

### TPEx OpenAPI
*Official EOD/reference source for TPEx.*
* **TWSE common stock:** `unsupported` (Different exchange).
* **TPEx common stock:** `supported_observed` (EOD data via mainboard daily close quotes).
* **TWSE ETF:** `unsupported`.
* **TPEx ETF:** `supported_candidate`.
* **TWSE TDR:** `unsupported`.
* **TWSE index:** `unsupported`.
* **TPEx index:** `unsupported` (Not supported by mainboard daily close quotes).
* **TAIFEX futures:** `unsupported`.
* **Mutual fund:** `unsupported`.
* **Foreign stock/ADR:** `unsupported`.
* **Broker account target:** `unsupported`.

### TWSE MIS
*Unofficial frontend endpoint, bounded low-frequency live watchlist source.*
* **TWSE common stock:** `supported_observed` (repo evidence exists).
* **TPEx common stock:** `supported_observed` (repo evidence exists).
* **TWSE ETF:** `supported_observed` (repo evidence exists).
* **TPEx ETF:** `supported_candidate`.
* **TWSE TDR:** `supported_observed` (repo evidence exists).
* **TWSE index:** `supported_observed` (e.g., TAIEX via `tse_t00.tw`, repo evidence exists).
* **TPEx index:** `supported_candidate`.
* **TAIFEX futures:** `unknown` (Lack of current repo evidence; likely unsupported or requires different channel structure).
* **Mutual fund:** `unsupported`.
* **Foreign stock/ADR:** `unsupported`.
* **Broker account target:** `unsupported`.
* **Caveats:** Session-cookie dependent, bounded watchlist only (do not use for full-market scans).

### Yahoo Finance
*Third-party public chart endpoint, low-frequency chart/watchlist context.*
* **TWSE common stock:** `supported_observed` (e.g., `2330.TW`, repo evidence exists).
* **TPEx common stock:** `supported_observed` (e.g., `8069.TWO`, repo evidence exists).
* **TWSE ETF:** `supported_observed` (e.g., `0050.TW`, repo evidence exists).
* **TPEx ETF:** `supported_candidate`.
* **TWSE TDR:** `supported_observed` (e.g., `9105.TW`, repo evidence exists).
* **TWSE index:** `supported_observed` (e.g., `^TWII`, repo evidence exists).
* **TPEx index:** `supported_candidate`.
* **TAIFEX futures:** `observed_unsupported` (e.g., `TX.TW` often returns HTTP 404 or missing data).
* **Mutual fund:** `observed_unsupported` (e.g., `FUNDA.TW` returns 404).
* **Foreign stock/ADR:** `supported_candidate` (Global coverage exists, but out of local Taiwan scope).
* **Broker account target:** `unsupported`.
* **Caveats:** Third-party, unofficial, coverage gaps exist.

### FinMind
*Commercial / third-party historical/EOD source.*
* **TWSE common stock:** `supported_observed` (Free tier / basic datasets, repo evidence exists).
* **TPEx common stock:** `supported_observed` (Free tier / basic datasets, repo evidence exists).
* **TWSE ETF:** `supported_candidate` (structurally plausible, but exact dataset behavior not directly verified for ETFs).
* **TPEx ETF:** `supported_candidate`.
* **TWSE TDR:** `supported_candidate` (structurally plausible, but exact dataset behavior not directly verified for TDRs).
* **TWSE index:** `supported_candidate` (Via index-specific datasets).
* **TPEx index:** `supported_candidate`.
* **TAIFEX futures:** `supported_candidate` (Requires distinct dataset parameters; current TX probes may fail without them).
* **Mutual fund:** `unknown` (dataset availability and authentication requirements require future verification).
* **Foreign stock/ADR:** `unknown` (outside current Taiwan-focused repo evidence; may require separate datasets or sources).
* **Broker account target:** `unsupported`.
* **Caveats:** Not a live watchlist source; subject to free-tier limits or auth requirements.

### Fugle MarketData / Fubon Neo API (Broker APIs)
*Authenticated execution-capable sources.*
* **All Target Classes:** `auth_required`.
* **Caveats:** Documented only in this repo; no live probing or execution behavior is authorized without credentials and explicit future scope.
