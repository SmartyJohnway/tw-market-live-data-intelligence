# M3E-01 Frontend Market Context View Design

## 1. Final Status

**M3E_01_COMPLETED_WITH_CAVEATS_READY_FOR_M3E_02**

This status reflects that the frontend design is fully specified to correctly render the required M3 caveats while adhering to the read-only constraint. Widespread target/source failures present in the generated offline mock artifacts are anticipated and must be rendered safely.

## 2. Files Inspected

- `frontend/public/index.html`
- `docs/protocol/M3E_FRONTEND_MARKET_CONTEXT_INPUT_CONTRACT.md`
- `docs/protocol/M3E_FRONTEND_CAVEAT_REGISTER.md`
- `docs/protocol/M3E_FRONTEND_DISPLAY_RULES.md`
- `docs/reviews/M3E_PREFLIGHT_01_FRONTEND_MARKET_CONTEXT_READINESS.md`

## 3. Frontend Entrypoint / Framework Assessment

The existing frontend structure located in `frontend/public/` currently uses Vanilla HTML/CSS/JS (no framework like React, Vue, or build tooling like Vite/Webpack). Specifically, `index.html` is a standalone static page that fetches static JSON (`matrix.json`) or triggers local network endpoints.

**Recommendation:** Maintain the current architecture (Vanilla HTML/CSS/JS) to preserve the static, easily reviewable nature of the frontend. Introducing a framework adds unnecessary build complexity for a simple read-only artifact viewer.

## 4. Proposed Route or Page Location

**Recommendation: Separate static page.**

Create a new file: `frontend/public/market-context.html`

Rationale:
- A separate page establishes a clear governance boundary for M3E read-only artifact viewing without commingling logic with the existing `index.html` (which currently has live API probe buttons).
- We will add a clear navigational link in `index.html` pointing to `market-context.html`.

## 5. Component Hierarchy

Since this will be implemented in Vanilla HTML/CSS/JS, "components" refer to distinct semantic DOM structures (e.g., `<section>`, `<div>`) managed by dedicated rendering functions in Javascript.

- `MainContainer`
  - `ContextStatusHeader` (Displays `generated_at_utc`, `generated_at_taipei`, `generation_mode`, `pack_version`)
  - `ScopeBanner` (Displays critical required language and `target_support_summary.bounded_watchlist_only`)
  - `AI_SafetyPanel` (Displays `ai_must_not_claim` and `ai_may_say`)
  - `DashboardGrid`
    - `SourceHealthAuthorityPanel` (Combines `source_health_summary` and `source_authority_summary`)
    - `LatestSnapshotSummaryPanel` (Displays `latest_snapshot_summary`)
    - `WatchlistObservationSummaryPanel` (Displays `watchlist_observation_summary`)
    - `FreshnessAndDelayPanel` (Displays `freshness_and_delay_summary`)
  - `FailedTablesContainer`
    - `FailedSourcesTable` (Iterates `failed_sources`)
    - `FailedTargetsTable` (Iterates `failed_targets`)
  - `AIBriefingPreview` (Renders parsed Markdown from `chatgpt_briefing.md`)
  - `CaveatFooter` (Displays `mandatory_caveats`)

## 6. Data-Loading Approach

Data will be loaded asynchronously via standard `fetch()` API calls when the page mounts (`window.onload` or `DOMContentLoaded`).

1. Fetch `../../research/generated/ai_context_pack.json`
2. Fetch `../../research/generated/chatgpt_briefing.md`
   *(Assuming the web server serves files from the repo root relative to the frontend. If served locally via a basic python http.server, paths may need adjusting. A static fetch is preferred. The frontend MUST NOT invoke endpoints that trigger python generator scripts).*
3. `latest_market_snapshot.json` and `watchlist_observations.json` don't necessarily need to be fetched directly unless specific granular details not present in the context pack summary are required. The input contract specifies using `ai_context_pack.json` for summary fields.

## 7. Exact Artifact-to-Component Mapping

Mappings derived from `M3E_FRONTEND_MARKET_CONTEXT_INPUT_CONTRACT.md`:

| Component | JSON Source / Field Path |
| :--- | :--- |
| **ContextStatusHeader** | `pack_version`, `generated_at_utc`, `generated_at_taipei`, `generation_mode` from `ai_context_pack.json` |
| **ScopeBanner** | `target_support_summary.bounded_watchlist_only`, `target_support_summary.full_market_coverage`, `target_support_summary.target_count` from `ai_context_pack.json` |
| **AI_SafetyPanel** | `ai_must_not_claim`, `ai_may_say` from `ai_context_pack.json` |
| **SourceHealthAuthorityPanel** | `source_health_summary.*`, `source_authority_summary.*` from `ai_context_pack.json` |
| **LatestSnapshotSummaryPanel** | `latest_snapshot_summary.market_session_status.*`, `latest_snapshot_summary.*` from `ai_context_pack.json` |
| **WatchlistObservationSummaryPanel**| `watchlist_observation_summary.*` from `ai_context_pack.json` |
| **FreshnessAndDelayPanel** | `freshness_and_delay_summary.*` from `ai_context_pack.json` |
| **FailedSourcesTable** | `failed_sources` (Array) from `ai_context_pack.json` |
| **FailedTargetsTable** | `failed_targets` (Array) from `ai_context_pack.json` |
| **AIBriefingPreview** | Raw text from `chatgpt_briefing.md` |
| **CaveatFooter** | `mandatory_caveats` from `ai_context_pack.json` |

## 8. Required Caveat Rendering

The UI must handle and persistently render the following caveats highlighted in PR #25:

- **Top Banner Level (Persistent & Prominent):**
  - `bounded_watchlist_only`: "This context is bounded to the configured watchlist."
  - `not_full_market_coverage`: "This is not full-market coverage."
  - `not_investment_advice`: "This is not investment advice."
  - `observations_are_not_signals`: "Observations are descriptive only and not trading signals."
  - "No official realtime quote guarantee is established."
  - `session_detection_not_implemented_in_m3a_02`: Display "Unknown Session" clearly if applicable.

- **Panel Level Warnings:**
  - `source_health_summary_describes_local_generated_source_state_only`: Note near source health that state is local/generated/offline.
  - `does_not_claim_current_live_production_source_availability`: Emphasize source health is not live production health.
  - `latest_snapshot_contains_no_successful_symbols`: Major warning fallback state if `latest_snapshot_summary.symbol_count == 0`.
  - `failed_sources_and_failed_targets_limit_summary`: Warning if failures > 0.

## 9. Empty / Missing / Failed-State Behavior

- If `ai_context_pack.json` fails to load (e.g. 404), the UI must display a critical full-page error indicating that "Context Artifacts are Missing. Run generator scripts to produce artifacts."
- Given the expected offline preflight state, the UI must gracefully render when `latest_snapshot_summary.symbol_count == 0` and `latest_snapshot_summary.failed_symbol_count == latest_snapshot_summary.target_count` (e.g., all 10 failed). The tables for Failed Targets and Sources must remain visible and prominently styled to indicate degradation.
- Empty arrays (e.g., `[]` for usable sources) must render as "None" or "0" without JS exceptions.

## 10. Styling and Layout Guidance

- Use CSS variables for consistent colors (Warning Yellow, Critical Red, Success Green).
- Utilize a clean, dashboard-style grid layout using CSS Grid or Flexbox.
- Delineate the boundary of the `AIBriefingPreview` using a distinct background color (e.g., light gray) or border to clearly separate AI-generated briefing text from structured deterministic metric panels.
- Emphasize tables when failed counts > 0 (e.g., light red tinted row backgrounds).

## 11. Accessibility and Responsive Behavior Notes

- Use semantic HTML tags (`<header>`, `<main>`, `<section>`, `<table>`, `<th>`).
- Ensure contrast ratios for warning texts are readable (WCAG AA).
- Ensure the layout degrades gracefully to a single column on narrow screens (e.g., mobile view), though the primary target is likely desktop evaluation.

## 12. Prohibited Wording Checklist

The UI must strictly avoid and ensure the text does NOT contain concepts related to:
- [x] "Buy", "Sell", "Hold" indicators
- [x] "Trading Dashboard" or "Screener"
- [x] "Real-time Live Quotes" (unless explicitly clarifying the lack thereof)
- [x] Target price predictions or rankings
- [x] Market-wide scanning assertions

## 13. Implementation Risks

- **File Fetching CORS / Paths:** Accessing files in `research/generated/` from `frontend/public/` via fetch might run into path resolution or CORS issues depending on how the frontend is locally served (e.g., direct `file://` vs `python -m http.server`).
  - *Mitigation:* Document the expected local server execution command for viewing the frontend (e.g., run `python -m http.server` from the repository root).
- **Markdown Parsing:** Rendering `chatgpt_briefing.md` safely without external network calls.
  - *Mitigation:* Render `chatgpt_briefing.md` as escaped plaintext inside a `<pre>` block by default. If Markdown rendering is later required, use only a repo-local / vendored parser or an already-existing local dependency, and require explicit authorization before adding it. Do not load Markdown libraries from CDN.

## 14. Recommended M3E-02 Implementation Milestone

**M3E-02-FRONTEND-MARKET-CONTEXT-VIEW-IMPLEMENTATION**
Objective: Implement the Vanilla HTML/JS design specified in M3E-01, creating `market-context.html` and hooking up the static fetch logic for the generated JSON/Markdown artifacts, ensuring all caveats and failure states are visibly rendered.

## 15. Confirmation of Non-Modification

**CONFIRMED:** No generated artifacts in `research/generated/` were modified during this milestone.

## 16. Confirmation of No Live Probes

**CONFIRMED:** No live network probes or upstream Python generator scripts were executed during this design milestone. All validations were strictly local and offline.
