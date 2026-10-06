# J-B03-S2C — TPEx `tpex_cmode` Unicode-Safe Value Recovery

**Disposition:** `J_B03_S2C_HOLD_AFFIRMATIVE_MARKER_SEMANTICS_UNPROVEN`

## One-shot observation

The single authorized GET succeeded: HTTP 200, `application/json`, 4,829 bytes, SHA-256 `b03d4d86ea689e3367be6224598897bb3da4ac4d13dfb77ce98c2088100a8d29`. Compatibility TLS retained `CERT_REQUIRED` and hostname verification. Strict UTF-8 decoding and JSON parsing passed. No literal U+FFFD occurred in decoded source strings.

The payload had 22 object rows and one source date. The date `1151006` parsed with the existing `scripts.twse_trading_calendar.parse_twse_roc_date` ROC_YYYMMDD precedent to `2026-10-06`, matching the retrieval date. `SecuritiesCompanyCode` remained a four-character string; all 22 observed codes were unique.

## Exact value recovered

`SuspensionOfTrading` was present as a string in all rows: 18 blank and 4 nonblank, with one distinct nonblank value. The exact value is fullwidth capital Y `Ｙ`, U+FF39:

| Representation | Value |
|---|---|
| `json_ascii` | `"\uff39"` |
| `unicode_escape` | `\uff39` |
| UTF-8 hex | `efbcb9` |
| Codepoints | `U+FF39` |
| Frequency | 4 |

The value is an encoded marker, not the literal field label `停止交易`. Neither the official metadata nor the repository's accepted source contract provides an authoritative mapping from U+FF39 to affirmative stopped trading. Therefore this tranche records the exact lexical value but does not assign positive semantics. A separately authorized authoritative marker definition is required before a “currently stopped” assertion may use it.

Blank remains unknown; target absence remains “no matching row in this special-status listing,” not normal trading. No negative tradeability claim is authorized.

The S2B and S2C hashes are identical, as are their row count and observed date. S2C recovers the exact value from that byte-identical payload without changing S2B's historical record.

## State and boundary

- `H0-SRC-01E` = OPEN; `H0-SRC-02` = OPEN.
- J-B03 = HOLD; J-B04 = BLOCKING; Phase J = NOT STARTED.
- One GET; retry/HEAD/POST/other market GET = 0. No raw response was persisted.
- No production, schema, catalog, routing, registry, activation, or MCP change; MCP remains 6.
- `data/` was untouched.

The adjacent JSON contains the complete ASCII-safe value representation and up to three reduced sample rows.
