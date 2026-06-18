# Yahoo Finance Taiwan Symbol Coverage

This document outlines the observed support and limitations for Taiwan market symbols when queried against the Yahoo Finance chart endpoint.

## Symbol Suffix Mappings

| Asset Type | Local Suffix Format | Yahoo Chart Suffix | Notes |
|---|---|---|---|
| TWSE Equities | `tse_{code}.tw` | `{code}.TW` | (e.g., `2330.TW`) |
| TWSE ETFs | `tse_{code}.tw` | `{code}.TW` | (e.g., `0050.TW`, `00929.TW`) |
| TPEx / OTC Equities | `otc_{code}.tw` | `{code}.TWO` | (e.g., `8069.TWO`, `5347.TWO`) |
| Indices | `tse_t00.tw` | `^{code}` | (e.g., `^TWII` for TAIEX) |

## Observed Coverage Classification

The system utilizes the following coverage classification statuses:

*   `observed_supported`: Verified to successfully parse and return data routinely.
*   `observed_unsupported`: Verified to return explicit errors (HTTP 404) or missing data consistently.
*   `candidate_requires_mapping`: Target exists locally but needs custom rules to translate to Yahoo schema.
*   `unknown`: Target has not been validated.

### 1. TWSE Listed Stocks (.TW)
**Classification**: `observed_supported`
**Examples**: `2330.TW`, `1435.TW`
**Notes**: Highly reliable, though subject to standard delayed polling constraints.

### 2. TWSE ETFs (.TW)
**Classification**: `observed_supported`
**Examples**: `0050.TW`, `00929.TW`
**Notes**: Reliably parsed via the standard `.TW` suffix.

### 3. TPEx / OTC Symbols (.TWO)
**Classification**: `candidate_requires_mapping` / `observed_supported`
**Examples**: `8069.TWO`, `5347.TWO`
**Notes**: Requires explicit `.TWO` translation from internal `otc_` tags.

### 4. Taiwan Indices
**Classification**: `observed_supported`
**Examples**: `^TWII`
**Notes**: Indices generally use `^` prefixing instead of country suffixes.

### 5. Futures (Placeholders)
**Classification**: `observed_unsupported`
**Examples**: `TX.TW`
**Notes**: Yahoo does not generally map TWSE futures logic directly to `.TW`. Queries strictly return HTTP 404 "Not Found". These are handled by the probe strictly as coverage limitations (`unsupported_targets`) to prevent false-positive code failure alerts.

### 6. Funds (Placeholders)
**Classification**: `observed_unsupported`
**Examples**: `FUNDA.TW`
**Notes**: Similar to futures, generic fund placeholders return HTTP 404 and are classified strictly as `unsupported_targets`.
