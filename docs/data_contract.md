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
  "retrieved_at_taipei": "2026-06-17T09:30:00.000000+00:00",
  "request": {
      "url": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
      "method": "GET",
      "params": {},
      "headers": {}
  },
  "http_status": 200,
  "http_ok": true,
  "parse_status": "success",
  "normalization_status": "success",
  "schema_fingerprint": {
      "type": "dict",
      "keys": ["exchange", "name", "price", "retrieved_at_taipei", "source_time_ms", "symbol"],
      "hash": "a1b2c3d4e5f6g7h8"
  },
  "schema_hash": "a1b2c3d4e5f6g7h8",
  "raw_sample_path": null,
  "normalized_sample_path": null,
  "raw_sample": { ... },
  "normalized_sample": { ... },
  "freshness_status": "realtime_candidate",
  "staleness_seconds": 15,
  "delay_status": "realtime",
  "requires_session": true,
  "requires_auth": false,
  "risk_level": "high",
  "risk_notes": ["Strict rate limiting", "Requires index.jsp visit for cookies", "Not designed for API use", "Unofficial endpoint"],
  "ai_suitability": "live_watchlist",
  "is_usable_now": true,
  "potentially_usable_with_credentials": false,
  "unsupported_targets": ["futures", "funds"],
  "failed_targets": [],
  "warnings": [],
  "errors": []
}
```

### Critical Fields for AI Context

- `retrieved_at_utc` & `retrieved_at_taipei`: The precise time the data was fetched from the endpoint, ensuring the agent knows exactly when the probe was run in both global and local contexts.
- `staleness_seconds`: Critical. Calculated by subtracting the data's native timestamp (if available, e.g., `source_time_ms` or `date`) from the current time. An AI MUST check this before assuming data is live.
- `freshness_status` & `delay_status`: Indicates if data is `realtime`, `delayed`, `eod`, `stale` or `unknown`.
- `contract_status`: Granular status replacing a simple boolean. Values include `http_pass`, `parse_pass`, `normalized_pass`, `doc_only`, `auth_required`, `blocked`, `failed`.
- `schema_fingerprint`: A structured object containing field inventory, top-level keys, normalized keys, and hash to detect API breaking changes. `schema_hash` is retained for backwards compatibility.
- `ai_suitability`: What task is this source best used for? e.g., `historical_and_eod`, `live_watchlist`.
- `is_usable_now`: Explicit boolean dictating whether an AI agent can currently execute this probe successfully.
- `potentially_usable_with_credentials`: Boolean dictating whether providing credentials would make it usable.
- `unsupported_targets` / `failed_targets`: Lists of asset classes or specific symbols that this source either intentionally does not support or recently failed to retrieve.