# M3G Controlled Live Probe Output Contract

## Purpose
This document defines the strict data contract for the output of bounded, controlled live network probes executed under the M3G Source Recovery framework. Live probe outputs are explicitly decoupled from production artifact generation to ensure safety and prevent uncontrolled data refresh.

## Scope & Non-Propagation Rule
- **Evidence Artifacts Only**: Outputs from controlled live probes are strictly considered evidence artifacts, not trading signals or production data.
- **Non-Propagation**: Live probe outputs **do not automatically update** `research/generated/*` or `frontend/public/*`.
- **Prohibited Interpretations**: Probe outputs must not be interpreted as full-market coverage, official realtime guarantees (unless from an official source and explicitly marked as such, which is rare/unsupported), or investment advice.

## Allowed Output Location
All controlled live probe outputs must be written to:
- `research/live_probe_runs/m3g_04/` (Current canonical path. Future milestones migrating to generic `research/controlled_live_probe_outputs/` must be explicitly authorized).

## Run Summary Schema

This top-level schema summarizes the execution of a bounded live probe run.

| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | string | ISO-8601 timestamp of the run. |
| `targets` | array | The specific subset of symbols probed (must adhere to M3G watchlist boundaries). |
| `sources_requested` | array | List of source IDs attempted during the run. |
| `results` | array | List of per-source output summary objects. |

**Example:**
```json
{
  "timestamp": "2024-05-20T10:00:00Z",
  "targets": ["2330", "0050"],
  "sources_requested": ["TWSE_MIS", "Yahoo_Finance"],
  "results": [
    {
       "source_id": "Yahoo_Finance",
       "status": "completed",
       "contract_status": "identity_mismatch",
       "http_ok": true,
       "parse_status": "success",
       "normalization_status": "failure",
       "failed_targets": ["2330"],
       "errors": ["Structured identity mismatch"],
       "output_file": "research/live_probe_runs/m3g_04/Yahoo_Finance_1715000000.json"
    }
  ]
}
```

## Per-Source Output Expectations

This schema defines the structured health and payload data expected from each individual source probed.

| Field | Type | Description |
| :--- | :--- | :--- |
| `source_id` | string | The identifier of the source (e.g., `TWSE_MIS`, `Yahoo_Finance`). |
| `status` | string | The overall probe attempt status for the source. |
| `contract_status` | string | The definitive status of the source's data contract compliance. |
| `http_ok` | boolean | Indicates if the HTTP network request(s) returned a 2xx success status. |
| `parse_status` | string | Indicates if the raw payload was successfully parsed (e.g., `success`, `failure`). |
| `normalization_status` | string | Indicates if the parsed payload was successfully normalized to M2 schemas. |
| `failed_targets` | array | List of target symbols that failed to retrieve or parse correctly. |
| `errors` | array | List of explicit error messages encountered. |
| `output_file` | string | Path to the raw or detailed output evidence file for this source. |

**Example:**
```json
{
  "source_id": "Yahoo_Finance",
  "status": "completed",
  "contract_status": "identity_mismatch",
  "http_ok": true,
  "parse_status": "success",
  "normalization_status": "failure",
  "failed_targets": ["2330"],
  "errors": ["Structured identity mismatch for 2330"],
  "output_file": "research/live_probe_runs/m3g_04/Yahoo_Finance_1715000000.json"
}
```

## Allowed Contract Statuses
The `contract_status` field must strictly use one of the following values, or specific errors derived from M2 validation:
- `normalized_pass`: The source passed all contract validation successfully.
- `identity_mismatch`: The source provided data, but identity fields (like company name) did not match expectations.
- `network_timeout`: The probe failed due to network constraints.
- `parse_error`: The payload shape deviated from the expected schema.
- `rate_limited`: The source responded with 429 or similar rate-limiting indicators.

## Freshness / Delay Semantics
All per-source normalized data must continue to populate standard delay semantics:
- `freshness_status`: Explicitly state whether the data is `eod`, `live_candidate`, or `delayed`.
- **EOD Warning**: `TWSE_OpenAPI` and `TPEx_OpenAPI` must strictly be classified as `eod` and never marked as realtime.
- **Stale Data Handling**: Stale outputs must be preserved as evidence but not treated as current market state in subsequent automation logic.
