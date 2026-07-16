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

