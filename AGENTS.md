# AGENTS.md — AI Collaboration Guide

## Project objective

Research and build an AI-native Taiwan live market data access workbench. The goal is to discover, validate, compare, and document reliable methods for obtaining Taiwan market data usable by AI assistants.

## Operating mode

This is a high-freedom research task. Do **not** assume a preferred solution. Do **not** force TWSE MIS as the answer. Explore, test, document, and compare.

## Current repository authority

This repository now contains accumulated source contracts, data-capability inventories, protocol documents, runtime helpers, tests, and acceptance reports. Current repository artifacts are authoritative when they are current and non-contradictory.

Before changing architecture, source semantics, AI exposure policy, or milestone direction, inspect the current main branch and relevant repository contracts first. Do not rely only on this AGENTS.md file or on task text.

At minimum, inspect relevant files under:

- `docs/data_capabilities/`
- `docs/protocol/`
- `docs/contracts/`
- `scripts/`
- `server/`
- `frontend/`
- `tests/`
- `config/`

Do not redefine established semantics from task text alone.
Search actual implementation paths rather than assuming file names.

## Required behavior

1. Prefer evidence over assumptions.
2. Keep raw probe results and failure reasons.
3. Distinguish official APIs, unofficial endpoints, commercial APIs, browser-rendered pages, and user-provided screenshots.
4. Never hardcode credentials or API keys.
5. Use low-frequency probing and avoid abusive access patterns.
6. Document timestamp semantics: source time, exchange time, retrieval time, delay status.
7. Preserve reproducibility: command, URL, headers, response status, response sample, and parsing method.
8. If a method is blocked, say exactly how and why.
9. Keep recommendations separate from raw findings.

## Strong prohibitions

- Do not claim a data source is real-time unless verified.
- Do not use yesterday's close as current market data.
- Do not bypass authentication or evade access control.
- Do not scrape aggressively.
- Do not commit `.env`, API keys, account credentials, cookies, or session tokens.

## Definition of done for any probe

A probe is not complete unless it records:

- source name,
- source type,
- URL or SDK/library,
- request method,
- required headers/cookies/session if any,
- status code,
- sample response or failure body,
- parsed fields,
- timestamp fields,
- freshness assessment,
- legal/maintenance risk,
- AI integration suitability.

A probe or source contract should also record:

- authority level,
- timing class,
- runtime integration status,
- AI exposure eligibility,
- whether the source is primary, reference-only, validation-only, credential-gated, or local product surface,
- whether the source may enter conversation context,
- whether the source is allowed to affect deterministic metrics,
- explicit forbidden interpretations.

## Suggested current workstream

Do not treat this project as a blank-slate source-discovery task. The current repository already has validated contracts, runtime observations, local product surfaces, and AI-context governance artifacts.

Prefer the current roadmap order unless repository evidence supports changing it:

1. Core runtime observation and AI context
   - TWSE_MIS runtime observation facts
   - TAIFEX_MIS runtime observation facts where available
   - M7B AI-safe market context projection
   - M7C deterministic metrics
   - bounded watchlist context
   - market clock / session state
   - frontend/operator workbench
   - M7 acceptance and E2E guardrails

2. Official reference and EOD context
   - TWSE_OpenAPI official EOD/reference context
   - TPEx_OpenAPI official EOD/reference context
   - TAIFEX_OpenAPI official derivatives EOD/statistical context
   - attention / disposition / trading restriction context
   - corporate action / ex-right / ex-dividend reference context

3. Optional historical or validation context
   - Yahoo Finance / Yahoo Taiwan Finance
   - FinMind
   - These sources are optional or supporting unless repository evidence upgrades them.
   - Do not use them to override official or runtime observations without explicit policy.

4. Credential-gated provider research
   - Fugle MarketData API feasibility
   - Fubon Neo API feasibility
   - Other broker/provider APIs
   - Never commit credentials, account details, tokens, cookies, or secrets.
   - Keep provider research separate from runtime integration until access, terms, schema, and local-secret handling are documented.

5. Local product surfaces and AI integration
   - FastAPI endpoints
   - MCP tools/resources
   - frontend/operator workbench
   - watchlist/conversation handoff
   - source-health reports
   - These are consumers or product surfaces, not external market-data sources.

6. High-risk research backlog
   - overseas reference context
   - ETF holdings / passive-flow research
   - broker-branch descriptive research
   - personal portfolio overlay
   - credential-gated providers
   - High-risk research must pass source-contract, timing-class, access, semantic-risk, and wording-guardrail review before entering runtime market context.

## Output discipline

Update the current authoritative repository artifacts. Prefer existing files and contracts over creating new parallel documents.

Common locations include:

- `docs/data_capabilities/`
- `docs/protocol/`
- `docs/contracts/`
- `docs/reviews/`
- `docs/operator/`
- `research/probe_log.md`
- `research/probe_runs/`
- `config/`
- `tests/`

Do not create outdated parallel files such as a new source catalog if the current repository already uses a more specific inventory or protocol document.

Do not create empty ornamental files. Add files only when they contain useful findings, contracts, evidence, tests, or acceptance decisions.
