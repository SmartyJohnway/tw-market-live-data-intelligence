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
