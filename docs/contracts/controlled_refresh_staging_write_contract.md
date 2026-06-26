# Controlled Refresh Staging Write Contract

## Purpose

This contract defines the governance, schema, and operator expectations for a future controlled-refresh staging-write path. It is design-only.

This milestone does **not** authorize staging write implementation. It does **not** authorize production refresh, frontend/public artifact refresh, research/generated artifact refresh, live probes, controlled live probe execution, full-market scans, broker/auth activation, commercial API enablement, trading signals, or realtime claims.

## Allowed Sources

Only already governed source IDs may be considered by a future implementation:

- `TWSE_OpenAPI` — official EOD reference source.
- `TPEx_OpenAPI` — official EOD reference source.
- `TWSE_MIS` — unofficial frontend endpoint; live candidate only with caveats, never a realtime guarantee.
- `Yahoo_Finance` — third-party context source with coverage, delay, and maintenance caveats.

FinMind, Fugle, Fubon, broker APIs, authenticated endpoints, credentials, cookies, tokens, and `.env` files are out of scope unless separately authorized later.

## Required Explicit Confirmation Flags

A future command must fail closed unless all required confirmations are present before any network access or write:

- `--confirm-controlled-refresh`
- `--confirm-staging-write-only`
- `--confirm-no-production-write`
- `--confirm-no-frontend-write`
- `--confirm-no-generated-artifact-write`
- `--confirm-no-trading-signal`
- `--confirm-bounded-targets`

## Staging Output Schema

A future staging output should be disposable and self-describing:

```json
{
  "schema_version": "controlled_refresh_staging_v1",
  "generated_at_utc": "ISO-8601 retrieval timestamp",
  "staging_only": true,
  "operator_confirmations": ["explicit flags supplied"],
  "target_universe": {"mode": "bounded", "symbols": []},
  "source_runs": [
    {
      "source_id": "TWSE_MIS",
      "source_type": "unofficial_frontend_endpoint",
      "authority_level": "official_eod|unofficial_frontend|third_party",
      "request_method": "GET or local_fixture",
      "url_or_fixture": "redacted URL or fixture path",
      "http_status": 200,
      "contract_status": "normalized_pass|failed|blocked|not_attempted",
      "retrieved_at_utc": "ISO-8601 retrieval timestamp",
      "source_timestamp": "ISO-8601 source timestamp or null",
      "freshness_status": "live_candidate|delayed|stale|eod_batch|unknown",
      "delay_status": "not_delayed_candidate|delayed_candidate|stale|eod|unknown",
      "staleness_seconds": 0,
      "normalization_status": "ok|partial|invalid|unknown",
      "data_quality_flags": [],
      "source_risk_flags": [],
      "normalized_sample_preview": {},
      "raw_evidence_ref": "staging-relative evidence path or null",
      "errors": []
    }
  ],
  "validation": {
    "network_authorized": false,
    "production_write": false,
    "frontend_write": false,
    "generated_artifact_write": false,
    "full_market_scan": false,
    "trading_signal": false
  }
}
```

## Validation Checks

A future implementation must validate:

1. Required confirmation flags are present.
2. Target universe is bounded and is not a full-market scan.
3. Output path is staging-only and does not overlap production, `frontend/public/*`, or `research/generated/*`.
4. No credentials, cookies, tokens, or `.env` files are read or written.
5. Each source records URL/fixture, request method, status, parsed fields, source timestamp, retrieval timestamp, freshness, delay, staleness, data quality flags, and source risk flags.
6. No buy/sell/hold, target price, ranking, automated action, or trading signal fields exist.
7. Staging outputs are not promoted into production current market state.
8. Failures preserve exact failure reasons.

## Write Prohibitions

- No production write.
- No frontend write.
- No generated artifact write.
- No staging write is implemented or authorized by this document.

## Rollback / Deletion Expectation

Staging output directories must be safe to delete as a complete unit. Deletion must not affect source code, committed evidence, production state, generated artifacts, or frontend artifacts.

## Stale/Freshness Caveats

`live_candidate` is not a realtime guarantee. Data may be stale, delayed, EOD-only, blocked, malformed, or missing. Consumers must display freshness and delay semantics before presenting price-like fields.

## Source Risk Flags

Future staging outputs must preserve source risk flags including unofficial source risk, fragile frontend contract risk, third-party coverage risk, official EOD reference-only caveats, and not-production-current-state caveats.

## Operator Checklist

- Confirm explicit authorization for the exact source list.
- Confirm a bounded target list.
- Confirm no production, frontend, or generated artifact write.
- Confirm no staging write unless separately implemented and authorized later.
- Run non-network validation first.
- Review failure modes and deletion plan.
- Keep recommendations separate from raw findings.

## Failure Modes

- Missing confirmation flag: fail closed.
- Unbounded target universe: fail closed.
- Path overlaps production/generated/frontend artifacts: fail closed.
- Credential/cookie/token requirement: fail closed.
- Source blocked, malformed, or stale: record failure/caveat, do not promote.

## Non-goals

- Implementing staging writes.
- Authorizing production refresh.
- Authorizing frontend/public artifact refresh.
- Authorizing research/generated artifact refresh.
- Authorizing live probes or controlled live probes.
- Enabling broker/auth/commercial APIs.
- Creating trading signals or realtime claims.
