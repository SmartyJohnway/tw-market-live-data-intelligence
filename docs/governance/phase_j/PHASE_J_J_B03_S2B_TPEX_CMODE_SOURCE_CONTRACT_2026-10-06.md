# J-B03-S2B — TPEx `tpex_cmode` Source Shape

**Disposition:** `J_B03_S2B_HOLD_POSITIVE_VALUE_GRAMMAR_UNPROVEN`

## One-shot result

The single authorized GET to `https://www.tpex.org.tw/openapi/v1/tpex_cmode` succeeded with HTTP 200 and `application/json`. The verified compatibility context retained `CERT_REQUIRED` and hostname checking, with `VERIFY_X509_STRICT` removed. The 4 MiB limit was applied; 4,829 bytes were read and hashed (`b03d4d86ea689e3367be6224598897bb3da4ac4d13dfb77ce98c2088100a8d29`). No redirect, retry, or second request occurred.

The response was a 22-object JSON array with one date and nine uniform fields. All expected names matched exactly, including the leading space in ` FinancialAnnouncements`. `SecuritiesCompanyCode` was a four-character numeric string on every row, with 22 unique codes and no duplicates. `Date` was the seven-digit string `1151006` on all rows; it is consistent with the retrieval date under ROC-calendar interpretation, but was not normalized.

## Blocking uncertainty

`SuspensionOfTrading` was present as a string on all 22 rows: 18 blank and 4 nonblank, with one distinct nonblank value. However, non-ASCII values in command output were replaced by unreadable glyphs. The exact value characters could not be preserved reliably, and the response was not persisted. Therefore the positive value cannot be mapped to “停止交易” with source-contract confidence. The other non-ASCII status fields have the same capture limitation. No second GET is authorized, so this record does not guess or reconstruct those values.

Blank remains unknown; it does not mean not stopped. Target absence means only no match in this special-status listing, not normal trading. No negative tradeability claim is supported.

## State and boundary

- `H0-SRC-01E` = OPEN; `H0-SRC-02` = OPEN.
- J-B03 = HOLD; J-B04 = BLOCKING; Phase J = NOT STARTED.
- No production, schema, catalog, routing, registry, activation, or MCP change; MCP remains 6.
- Market GET = 1; retry/HEAD/POST/other market GET = 0. The raw body was transient and not saved; `data/` was untouched.

A future source-shape authorization would need to ensure exact Unicode value preservation on the single response. This hold does not authorize another request or implementation.

Full telemetry and aggregate field/value counts are in the adjacent JSON record.
