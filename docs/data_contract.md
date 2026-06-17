# Data Contract

Target normalized schema for market snapshot data.

## MarketSnapshot

| Field | Type | Required | Description |
|---|---|---:|---|
| source | string | Yes | Data source name |
| symbol | string | Yes | Canonical symbol, e.g. TAIEX, 2330.TW |
| exchange | string | No | TWSE, TPEx, TAIFEX, etc. |
| name | string | No | Human-readable name |
| price | number | Yes | Last/current value |
| change | number | No | Absolute change |
| change_pct | number | No | Percentage change |
| open | number | No | Open price |
| high | number | No | Intraday high |
| low | number | No | Intraday low |
| previous_close | number | No | Previous close |
| volume | number | No | Volume if available |
| turnover | number | No | Turnover / traded value |
| source_timestamp | string | Yes | Timestamp reported by source |
| retrieved_at | string | Yes | Local retrieval timestamp |
| delay_status | string | No | realtime, delayed, unknown, close_only |
| raw | object | No | Optional raw payload reference |

## Rule

Never mix current intraday data with prior-day close without labeling it clearly.
