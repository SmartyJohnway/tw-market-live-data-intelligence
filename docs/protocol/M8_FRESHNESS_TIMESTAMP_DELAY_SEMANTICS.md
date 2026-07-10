# M8 Freshness Timestamp Delay Semantics

- **Status**: `m8_freshness_timestamp_delay_semantics.v1_defined`

M8-00-02 defines semantics only. It does not implement the evaluator yet. The evaluator belongs to `M8-00-04-SOURCE-FRESHNESS-EVALUATOR-PURE-HELPER`.

## Required terms

- `source_timestamp`: Timestamp supplied by the source payload or source metadata, if present.
- `retrieved_at_utc`: UTC time when the local system retrieved, received, loaded, or observed the source artifact.
- `market_date`: Market calendar date represented by a source record.
- `trading_date`: Trading-session date represented by a source record.
- `session_state`: Open, closed, pre-open, post-close, holiday, unknown, or another policy-defined session label.
- `delay_seconds`: Computed or declared delay between source time and retrieval time when such computation is valid.
- `freshness_assessment`: Policy label describing currentness without turning source data into advice.
- `freshness_reason`: Human-readable reason for the freshness assessment.
- `stale_reason`: Human-readable reason a source is stale.
- `source_unavailable_reason`: Human-readable reason a source is unavailable.
- `not_realtime_guaranteed`: Boolean or caveat stating that realtime status is not guaranteed.
- `eod_only`: Boolean or caveat stating a source is end-of-day only.
- `intraday_snapshot`: Boolean or caveat stating the source is a bounded intraday snapshot.
- `manual_snapshot`: Boolean or caveat stating evidence came from operator-provided artifact or screenshot-like local evidence.
- `validation_only`: Boolean or caveat stating a source can support validation only and is not primary context.
- `credential_gated`: Boolean or caveat stating credentials are required and must not be committed.
- `official_reference_date`: Date associated with an official reference or EOD record.
- `exchange_timestamp_absent`: Boolean or caveat stating no exchange timestamp is available.
- `retrieved_time_only`: Boolean or caveat stating only local retrieval/load time is available.

## Freshness assessment enum

- `fresh_intraday_snapshot`
- `stale_intraday_snapshot`
- `official_eod_reference`
- `official_statistics_eod`
- `regulatory_reference`
- `manual_snapshot`
- `validation_only`
- `credential_gated_metadata_only`
- `source_unavailable`
- `unknown`

## Interpretation rules

- `retrieved_at_utc` is not automatically exchange timestamp.
- retrieved_at_utc is not exchange timestamp unless the source contract explicitly proves that equivalence.
- EOD must not be realtime; an EOD source must not be described as realtime.
- official_statistics_eod must not be described as live derivatives signal.
- manual_snapshot must not be described as official exchange source.
- validation_only source must not be used as primary context.
- unknown freshness must force caveated wording.
- stale source must not be described as current market.
- no trading advice, trading signal, recommendation, target price, or support/resistance interpretation may be produced from freshness labels.
