# Output Contract

The CLI exposes three separate machine schemas. Never infer one schema from another.

## 1. `ResolutionResult`

Used only by `classifier.py --query QUERY`:

```json
{
  "operation": "resolve",
  "query": "1111",
  "resolution_status": "resolved_exact_code",
  "candidate_count": 1,
  "candidates": [],
  "caveats": []
}
```

`candidates` contains zero or more `ClassificationRecord` objects. Exact matches still use the candidates array; they are not flattened into the top level. Schema: `schemas/resolution-result.schema.json`.

## 2. `ClassificationRecord`

One normalized classification, with no query-resolution metadata:

```json
{
  "identity": {
    "security_code": "1101",
    "security_name_zh": "台泥",
    "security_name_en": "TCC",
    "isin": "TW0001101004",
    "cfi": "ESVUFR"
  },
  "classification": {
    "asset_class": "equity",
    "instrument_family": "company_share",
    "instrument_type": "common_share",
    "equity_subtype": "ordinary",
    "market": "twse",
    "board": "main",
    "listed_common_stock_core_flag": true,
    "classification_status": "confirmed_dual_lane",
    "cfi_mapping_version": "controlled-prefix-v1.1.0",
    "cfi_mapping_scope": "partial_controlled_prefixes_not_full_iso_10962",
    "cfi_decode_depth": "category_or_group_prefix_only",
    "reason_codes": [],
    "conflicts": []
  },
  "dates": {},
  "observation": {
    "status": "observed_in_latest_verified_snapshot",
    "observed_at": "YYYY-MM-DDTHH:MM:SS+08:00",
    "source_updated_date": "YYYY-MM-DD"
  },
  "lifecycle_events": [],
  "evidence": [],
  "conflicts": [],
  "caveats": []
}
```

Schema: `schemas/classification-result.schema.json`.

## 3. `BatchClassificationReport`

Used only by `classifier.py --all`:

```json
{
  "operation": "classify_all",
  "record_count": 5,
  "records": [],
  "caveats": []
}
```

Every member of `records` must satisfy `ClassificationRecord`. Schema: `schemas/batch-classification-report.schema.json`.

## Observation provenance

Allowed values:

- `observed_in_capture`: seen in a supplied capture, freshness not independently established.
- `observed_in_latest_verified_snapshot`: a fresh official probe or explicit latest-snapshot verification established freshness.
- `fixture_observation_only`: bundled regression evidence; never living truth.
- `historical_capture`: explicitly historical capture.

The presence of `source_updated_date` alone never authorizes `observed_in_latest_verified_snapshot`.

## Resolution statuses

```text
resolved_exact_isin
resolved_exact_code
resolved_exact_name
ambiguous
not_found
source_blocked
quarantined
```

## Human-readable response

When relevant, report resolution, identity, classification, observation provenance, key dates with semantics, lifecycle events, official evidence, conflicts, and caveats. Do not call a security actively tradable merely because it appears in an ISIN snapshot.
