# Data Contract

To ensure that AI systems can properly use Taiwan equity market information without risk of hallucinations or trading on stale data, all probes must standardize around the following data contract envelope.

## Standard Envelope

```json
{
  "probe_id": "twse_mis_20260617_093000",
  "source": "TWSE_MIS",
  "source_type": "unofficial_frontend_endpoint",
  "contract_status": "normalized_pass",
  "retrieved_at_utc": "2026-06-17T01:30:00.000000+00:00",
  "status": "pass",
  "http_status": 200,
  "url": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
  "method": "GET",
  "request_params": {},
  "headers_used": {},
  "requires_session": true,
  "requires_auth": false,
  "schema_hash": "a1b2c3d4e5f6g7h8",
  "raw_sample": { ... },
  "normalized_sample": { ... },
  "freshness_status": "realtime_candidate",
  "staleness_seconds": 15,
  "risk_level": "high",
  "risk_notes": [],
  "ai_suitability": "live_watchlist"
}
```

### Critical Fields for AI Context

- `retrieved_at_utc`: The time the data was fetched from the endpoint, ensuring the agent knows exactly when the probe was run.
- `staleness_seconds`: Critical. Calculated by subtracting the data's native timestamp (if available, e.g., `source_time_ms` or `date`) from the current time. An AI MUST check this before assuming data is live.
- `freshness_status`: One of `realtime_candidate`, `eod_batch`, `delayed_15m`, or `unknown`.
- `contract_status`: Granular status replacing a simple boolean. Values include `http_pass`, `parse_pass`, `normalized_pass`, `doc_only`, `auth_required`, `blocked`, `failed`.
- `schema_hash`: A fingerprint of the returned keys to detect silent API breaking changes.
- `ai_suitability`: What task is this source best used for? e.g., `historical_and_eod`, `live_watchlist`.
