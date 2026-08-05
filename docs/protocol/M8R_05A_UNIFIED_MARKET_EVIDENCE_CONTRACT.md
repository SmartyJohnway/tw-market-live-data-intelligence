# M8R-05A: Unified Market Evidence Contract

This protocol defines the formal Facade contract between the AI and the deterministic project layer (`tw-market-live-data-intelligence`).

## 1. Intent and Philosophy

The core goal is to allow the AI to freely understand user requests and decide what evidence is needed to answer them, while delegating the safe, auditable, and deterministic retrieval of that evidence to the project code.

We **DO NOT** use:
- Fixed intent enumerations (e.g., `CURRENT_PRICE_QUERY`).
- Keyword-based data routing.
- Investment conclusion fields (e.g., `bullish`, `bearish`).

Instead, we use **Composable Evidence Needs**.

## 2. System Boundaries

### AI Responsibilities:
- Understand user intent.
- Extract target strings (without guaranteeing exact canonical resolution).
- Determine required and optional evidence needs based on the question context.
- Assess currentness requirements.

### Project Code Responsibilities:
- Validate request schemas.
- Resolve target strings to canonical identities securely.
- Evaluate capabilities and enforce bounds.
- Map requested evidence needs to internal 03D plans and 03E packages.
- Execute network calls (outside the scope of this M8R-05A definition).
- Guarantee evidence currentness semantics.
- Deliver results with citations, caveats, and audit references.

## 3. Evidence Need Vocabulary

The following evidence needs are defined in the vocabulary:

- **`identity`**: Requests the canonical security identity (e.g., security code, market).
- **`current_observation`**: Requests the latest available market data (liveish/current snapshot), not guaranteed realtime.
- **`official_eod_reference`**: Requests the official EOD record, enforcing strict validation of expected completion dates and session statuses.
- **`recent_performance`**: Requests descriptive performance metrics over a specified lookback period (e.g., 20 trading days).
- **`session_status`**: Requests the market session context, local clock, and closure states.
- **`source_currentness`**: Requests the metadata concerning the retrieval timestamp, effective trade date, and timing class.
- **`evidence_quality`**: Requests details on data coverage, partial results, and available fallbacks.

## 4. Contract Artifacts

- **Request Schema**: `unified_market_evidence_request.v1`
- **Preview Schema**: `unified_market_evidence_preview_response.v1`
- **Result Schema**: `unified_market_evidence_result.v1`
- **Capability Catalog Schema**: `unified_market_evidence_capability_catalog.v1`

## 5. Market Support Maturity

Supported markets are mapped into explicit support levels in the Capability Catalog:
- **TWSE**: `supported`
- **TPEX**: `supported_with_caveats` (closure authority caveats apply).
- **TAIFEX**: `provisional` (day session provisional; night session unsupported).

## 6. Execution Modes and Safety

The request allows `preview` and `execute` modes. The current profile for M8R-05A enforces explicit approval logic through the `preview` flow. 

**Prohibited Internal Fields in Request:**
The AI MUST NOT specify internal execution details in its requests, including but not limited to `source_family`, `adapter`, `route`, `endpoint`, `03c_bundle`, or `operation_id`. All such internal mapping is solely the responsibility of the deterministic project layer.

## 7. Result Schema Completion (M8R-05C)

M8R-05C completed the `unified_market_evidence_result.v1` schema with the following additive fields:

### New Required Fields
- **`result_id`** (`umeresult-v1-*`): Deterministic result identity computed from `request_id + receipt_id + bundle_id`.
- **`result_hash`**: SHA-256 of the canonical result body (excluding itself).
- **`generated_at`**: Inherited from `receipt.finalized_at` or explicit CLI parameter.
- **`request_summary`**: Deterministic projection of request fields (mode, target count, data needs).

### Extended `audit_reference`
The `audit_reference` now requires `audit_package_id`, `schema_version`, and `relative_path` linking to the separate audit package (`unified_market_evidence_audit_package.v1`).

### New Optional Fields
- **`derived_metrics`** per target: Deterministic metric calculations with explicit status, input references, and calculation version.
- **`fallback_state`** in evidence_envelope: String classification of fallback type.
- **`derived_metrics`** definition: Schema-validated metric objects with `metric_id`, `status` (available/unavailable/invalid/not_requested), `value`, `method`, `formula_or_definition`, `input_evidence_references`, `calculation_version`, `calculated_at`.
- **`partial_failures[].data_need`** and **`partial_failures[].reason_code`**: More precise failure attribution.

### New Audit Package Schema
A separate `unified_market_evidence_audit_package.v1` schema was added for operator/replay/debug evidence. It contains operation lineage, artifact inventory, citation-to-operation mapping, integrity verification, and replay manifest. It is never embedded in the AI-context result.

### Compatibility
All changes are additive. The `schema_version` remains `unified_market_evidence_result.v1`. No v2 migration is required. Existing test fixtures were updated to include the new required fields.
