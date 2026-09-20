# Phase H Product Boundary and Anti-Scope-Creep Contract

Status: **FROZEN**  
Freeze date: 2026-09-21  
Phase G baseline: `aa315918e0b5b431f4e63334c3ff91eac4e4e8f5`  
Owner review: `H0-01A ACCEPTED_WITH_MINOR_AMENDMENT`

## 1. Normative role

TW-Market is **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**. Phase H has one role: **Interpretation Safety**.

Phase H MUST provide bounded official interpretation-critical evidence for securities involved in the current conversation. It MUST prevent correct market observations from being misinterpreted because official trading-status, price-basis, coverage, or recent-reference context is missing.

Canonical North Star:

> Phase H does not create historical market-data research infrastructure. Phase H allows an AI, during a specific Taiwan-equity conversation, to request a bounded set of official evidence required to avoid misinterpreting current or recent market observations.

## 2. Execution boundary

Every Phase H acquisition MUST be:

- explicit;
- target-scoped;
- data-need-scoped;
- time-bounded;
- authorized;
- execute-once;
- auditable.

Phase H MUST NOT introduce startup market fetch, hidden acquisition, background refresh, default polling, an internal scheduler, automatic historical backfill, or market-wide acquisition for later use.

Preview and validation MUST remain zero-network. Network execution MUST occur only after the existing Unified authorization boundary is satisfied.

## 3. Persistence boundary

Phase H MAY persist only evidence needed to prove one authorized request:

- normalized target-bounded evidence;
- source provenance and source-contract identity;
- content hashes;
- citations and lineage;
- authorization, receipt, operation result, Result and Audit artifacts;
- bounded diagnostics needed to explain a governed failure.

Phase H MUST NOT require or create:

- a persistent OHLCV warehouse;
- a market-wide daily archive;
- a corporate-action warehouse;
- an adjusted-price database;
- a historical factor database;
- automatic local accumulation;
- retained full-market source payloads beyond transient bounded resolution needs.

## 4. Analysis boundary

Phase H MAY emit:

- official facts;
- source, publication, effective and observation timing;
- declared coverage and missing states;
- deterministic descriptive calculations;
- deterministic interpretation-safety states;
- source-faithful caveats.

Phase H MUST NOT emit or calculate buy, sell, hold, bullish, bearish, target price, trading signal, technical-analysis indicator, stock ranking, strategy output, return prediction, investment recommendation, or unsupported causal attribution.

## 5. AI and TW-Market responsibility split

The AI:

- understands the conversation;
- selects targets, evidence needs and bounded time scope;
- interprets governed evidence;
- writes the human-facing answer.

TW-Market:

- validates the Unified Request;
- resolves existing Security Master identity;
- plans and previews;
- enforces authorization;
- executes once;
- retrieves approved official evidence;
- validates, normalizes and binds it;
- calculates only deterministic context;
- records timing, coverage and missing states;
- creates citations, lineage and audit evidence;
- fails closed.

TW-Market MUST NOT invent a parallel identity authority, parallel planner, source fact, event relationship, or official determination.

## 6. Exact anti-scope rule

**MUST / MUST NOT**

Phase H does not create a historical market-data database.

Historical observations MUST be acquired only when required by an explicitly authorized, target-scoped, time-bounded Unified Request.

No automatic history backfill, daily collection, background refresh, market-wide archive, adjusted-price database, technical-analysis engine, strategy engine, or backtesting capability is introduced by Phase H.

Insufficient official-source coverage MUST be represented as an evidence limitation. It MUST NOT be repaired through hidden acquisition, unofficial substitution, search ingestion, or silent accumulation.

## 7. Existing authority preserved

Phase H MUST preserve:

- Security Master durable identity semantics;
- explicit market plus exact security-code source binding;
- existing Unified authorization and execute-once boundaries;
- historical V1/V2 artifact readability and byte authority;
- exactly six MCP tools.

Phase H MUST NOT introduce a seventh MCP tool. H1 and H2 evidence MUST flow through existing Unified Request `data_needs` after later exact-schema authorization.

## 8. Freeze boundary

This contract freezes product meaning only. It does not authorize production implementation, source adapters, runtime registration, Catalog/Route activation, Workbench changes, MCP behavior changes, or V3 schema bytes.

H0-E, H0-F, H0-G and H0-H remain DEFERRED.

## 9. Provenance

Inputs:

- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Official_Source_Transport_Automation_Authority_Matrix.md`
- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Source_Authority_Matrix.json`

Accepted pre-amendment SHA-256 values:

- Markdown: `566a91f5c7fa1da18dfb85753a19ba6f446973a5dc8040a3ac7996dde0fe31d3`
- JSON: `6a05968b4e2c6bd444bd90942eaffd9f24a55c99b17bd29365211ea3c5cd53f7`

Post-amendment SHA-256 values:

- Markdown: `120cd0278484b429cf618e9041b2bd0eb56edb0e43cee17d00be0af03347b7ef`
- JSON: `6685c236274b662107c0061240f6983e63ce68dee6daa33c1c3e2deef1ef7670`

This file's hash is recorded in `PHASE_H_H0_A_D_FREEZE_MANIFEST.json`.
