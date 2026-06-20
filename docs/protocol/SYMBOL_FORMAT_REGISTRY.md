# Symbol Format Registry

This registry documents how the same conceptual target is represented across different data sources. Formats vary wildly, from raw numeric codes to exchange-prefixed strings and specialized channel identifiers.

## Known Source Formats

* **TWSE MIS:** Channel format, typically `<venue>_<symbol>.tw` (e.g., `tse_2330.tw`, `otc_8069.tw`).
* **Yahoo Finance:** Ticker with exchange suffix (e.g., `2330.TW`, `8069.TWO`, `^TWII`).
* **TWSE OpenAPI:** Raw code format, usually just the numeric symbol for matching `Code` fields (e.g., `2330`).
* **TPEx OpenAPI:** Raw code format, usually matching `SecuritiesCompanyCode` fields (e.g., `8069`).
* **FinMind:** Dataset symbol format, usually the raw code (e.g., `2330`).
* **Broker API:** Highly dependent on the broker. Often documented as a placeholder format unless explicit credentials and API spec are available.

## Expected Mapping Examples

### 2330 台積電 (TWSE common stock)
* **TWSE MIS:** `tse_2330.tw`
* **Yahoo Finance:** `2330.TW`
* **TWSE OpenAPI:** `2330`
* **TPEx OpenAPI:** `unsupported`
* **FinMind:** `2330`
* **Broker API:** candidate (varies by broker)

### 8069 元太 (TPEx common stock)
* **TWSE MIS:** `otc_8069.tw`
* **Yahoo Finance:** `8069.TWO`
* **TWSE OpenAPI:** `unsupported`
* **TPEx OpenAPI:** `8069`
* **FinMind:** `8069`
* **Broker API:** candidate (varies by broker)

### 0050 元大台灣50 ETF (TWSE ETF)
* **TWSE MIS:** `tse_0050.tw`
* **Yahoo Finance:** `0050.TW`
* **TWSE OpenAPI:** `0050`
* **TPEx OpenAPI:** `unsupported`
* **FinMind:** `0050`
* **Broker API:** candidate (varies by broker)

### 00929 復華台灣科技優息 ETF (TWSE ETF)
* **TWSE MIS:** `tse_00929.tw`
* **Yahoo Finance:** `00929.TW`
* **TWSE OpenAPI:** `00929`
* **TPEx OpenAPI:** `unsupported`
* **FinMind:** `00929`
* **Broker API:** candidate (varies by broker)

### 5347 世界 (TPEx common stock)
* **TWSE MIS:** `otc_5347.tw`
* **Yahoo Finance:** `5347.TWO`
* **TWSE OpenAPI:** `unsupported`
* **TPEx OpenAPI:** `5347`
* **FinMind:** `5347`
* **Broker API:** candidate (varies by broker)

### 9105 泰金寶-DR (TWSE TDR)
* **TWSE MIS:** `tse_9105.tw`
* **Yahoo Finance:** `9105.TW`
* **TWSE OpenAPI:** `9105`
* **TPEx OpenAPI:** `unsupported`
* **FinMind:** `9105`
* **Broker API:** candidate (varies by broker)

### TAIEX (TWSE index)
* **TWSE MIS:** `tse_t00.tw`
* **Yahoo Finance:** `^TWII`
* **TWSE OpenAPI (STOCK_DAY_ALL):** `unsupported`
* **TPEx OpenAPI:** `unsupported`
* **FinMind:** candidate (via specific index dataset)
* **Broker API:** candidate

### TX 台指期 (TAIFEX index future)
* **TWSE MIS:** `unknown` / `unsupported`
* **Yahoo Finance:** `TX.TW` (often `observed_unsupported` or erratic)
* **TWSE OpenAPI:** `unsupported`
* **TPEx OpenAPI:** `unsupported`
* **FinMind:** candidate (requires specific futures dataset parameters)
* **Broker API:** candidate (often requires distinct futures API)

## Fallback Values
For targets where the exact format is not directly known or observed, we use standard placeholders:
* `candidate`: Plausible format based on source documentation, but needs live verification.
* `requires_verification`: Known to exist but specific format strings are debated or inconsistent.
* `unsupported`: Known that the source does not support this target class.
* `unknown`: Not enough evidence to suggest a format.
