# M8 Post-M8C Revised Roadmap

Baseline SHA: `bd3496efe7492e6cd3c7dacc169e142f90e6cd92`.

Controlling principle: The repository provides governed market evidence, deterministic calculations, timing semantics, provenance, and controlled data access. The Agent or human discussion layer decides how that evidence is interpreted, discussed, compared, or converted into an opinion. Evidence integrity remains strict. Conversation behavior is not hard-coded into the market-data core.

Dependency order is Phase A through Phase O; recording a phase is not approval to implement it in R1.

## Phase A — Existing governance-core convergence

M8R-03E completion; repository roadmap/registry realignment; repository-wide health audit; critical remediation gating.

## Phase B — AI Capability Guide and Agent Skill

quick capability guide; full capability contract; portable Agent Skill; tool-selection examples; time/source semantics guidance.

## Phase C — Unified Market Evidence Tool API

simple AI-facing request; simple evidence response; audit response; capability catalog; internal orchestration over existing 03C/03D/03E layers.

## Phase D — Temporary Conversation Target Resolution

AI-extracted target candidates; strict resolver; resolved/ambiguous/not-found output; conversation-local target set; no implicit persistent-watchlist mutation.

## Phase E — Agent/MCP integration

describe_capabilities; resolve_targets; preview_market_evidence_request; execute_market_evidence_request; read_evidence_package; authorization UX; closed-loop fixtures.

## Phase F — Watchlist and user-facing productization

persistent watchlist storage/versioning; local-first service API; watchlist and evidence UI.

### M8R-08G pre-Phase-F architecture realignment

Before Phase F durable storage begins, the Taiwan Market Identity Service and
installation-local Security Master release lifecycle are the governing identity
boundary.  Cash instruments use ISIN as their durable instrument identity while
`MARKET:CODE` remains the listing and execution-routing identity.  Releases are
explicitly built, qualified, atomically activated and rollback-capable in the
local installation; a clean installation is legally `NOT_INITIALIZED` and has
no Candidate-B fallback.  This combined 08G-01 tranche covers identity contract,
release lifecycle, and consumer migration.  It does not start watchlist storage.

**Status: CLOSED.**  M8R-08G portability, portable-Skill realignment, clean-clone
acceptance, and installation-local bootstrap are recorded in
`docs/reviews/M8R_08G_PRE_PHASE_F_PORTABILITY_AND_SKILL_REALIGNMENT_CLOSURE.*`.
The next authorized action is `READY_TO_BEGIN_M8R_09_PREFLIGHT`; M8R-09
implementation and Phase F storage remain unstarted.

### M8R-09 persistent watchlist storage and versioning

**Status: CLOSED.**  Installation-local SQLite watchlist storage now has
ISIN durable cash identity, typed preview/commit mutations, optimistic version
checks, immutable hash-chained revisions, legacy M5N/M5K import, rollback,
export, and a minimal local FastAPI surface.  It does not add MCP mutation,
market execution, background work, or a frontend persistence UX.  The closure
evidence is `docs/reviews/M8R_09_PERSISTENT_WATCHLIST_STORAGE_AND_VERSIONING_IMPLEMENTATION_CLOSURE.*`.
The next authorized action is `READY_FOR_M8R_10_PREFLIGHT`; M8R-10
implementation remains unstarted.  Phase F is the planned v1.0 feature-freeze
boundary only; formal v1.0 release remains subject to separate release-readiness
and contract-freeze review.

### M8R-10 watchlist and evidence Workbench integration

**Status: CLOSED.**  The canonical `/workbench/` now integrates M8R-09
persistent watchlists, temporary targets, deterministic mixed-target selection,
Unified Request v1 composition, exact-version selection provenance, the existing
Mode A/B/C execute-once path, and AI handoff.  Persistent mutation, evidence
authorization, and network execution remain three separate explicit confirmation
domains.  Closure evidence is recorded in
`docs/reviews/M8R_10_WATCHLIST_AND_EVIDENCE_WORKBENCH_INTEGRATION_IMPLEMENTATION_CLOSURE.*`.

**Phase F status: CLOSED.  V1 feature complete.** V1 release-readiness implementation is complete. The immutable `v1.0.0-rc.1` prerelease is published; its exact RC provenance remains recorded in `docs/reviews/V1_0_RELEASE_READINESS_IMPLEMENTATION_AND_RC_CANDIDATE_PREPARATION_CLOSURE.*`. The repository is preparing final ProductVersion `1.0.0`; the latest stable GitHub Release remains `v0.1.0`. Final v1.0.0 has not yet been published. Phase G is **NOT STARTED**.

## Phase G — Dynamic Research Evidence

MOPS disclosures; official fundamentals/financial statements; dynamic research sources; multi-source research evidence packages.

## Phase H — Long-running operation and automation

scheduled refresh; security-master refresh; watchlist monitoring; notifications; bounded agent workflows.

## Phase I — Minimal Quote Interpretation Enrichment

attention/disposition/trading restrictions; corporate-action reference-price context; unified quote-interpretation context.

## Phase J — Recent Historical Reference Baseline

5D/20D ranges; 5D/20D average volume; current position in range; relative volume; corporate-action-safe comparison.

## Phase K — Spot-Derivatives Descriptive Context

spot bounded observation; front-month derivative bounded observation; official settlement reference; Put/Call Ratio; large trader OI; timing alignment; optional loading.

## Phase L — Scenario Acceptance and Interpretation Validation

normal TWSE target; TPEx identity through TWSE MIS otc route; TAIFEX current unavailable with EOD fallback; stale evidence; partial success; corporate action; regulatory restriction; historical baseline; spot/derivatives timing mismatch.

## Phase M — Multi-Agent Capability Evaluation

ChatGPT; Codex; Claude; Gemini; Hermes Agent; OpenCode.

## Phase N — Advanced Optional Evidence Enrichments

market breadth; industry context; index membership; ETF/component relationships; official financing/securities-lending/day-trading statistics; other optional context after explicit review.

## Phase O — Production Hardening

observability; trace IDs; artifact replay; retention; schema migration; load testing; resource limits; security review; source-drift detection.


## M8R-03E-R2 update

R2-F0 and R2 are recorded as GO_WITH_CAVEATS from baseline `1c2144498b524e52b2bf21fce8ed00683d9eb3a7`; the combined PR disposition is APPROVE_WITH_CAVEATS. The active implemented-through track is `M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION`, and the active successor is `M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP`. Phase C remains `blocked_pending_M8R-03E-R3-critical-subset` / `blocked_pending_R3_critical_subset` for the R3 AI behavior/evidence schema decoupling work. R2 filesystem containment is remediated with portable TOCTOU and Windows reparse caveats; GitHub runner execution was not performed under NO_GITHUB_CI.
