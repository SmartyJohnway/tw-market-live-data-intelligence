# Phase H H1 Trading Status Context Contract

Status: **FROZEN**  
Freeze date: 2026-09-21  
Capability: `trading_status_context`  
Phase G baseline: `aa315918e0b5b431f4e63334c3ff91eac4e4e8f5`  
Owner review: `H0-01A ACCEPTED_WITH_MINOR_AMENDMENT`

## 1. Purpose and boundary

`trading_status_context` MUST report instrument-specific official supervisory or trading-restriction evidence. It MUST remain separate from `session_status`, which represents market-level clock, trading-day and closure context.

H1 MUST report exchange determinations. It MUST NOT compute whether a security should be under attention or disposition, reproduce an exchange surveillance algorithm, assign severity or abnormality scores, or infer risk rankings.

## 2. Frozen subtypes

The initial canonical subtype vocabulary is:

- `attention`;
- `disposition`;
- `changed_trading_method`;
- `suspension`;
- `resumption`.

Source-specific flags MAY be retained as source-native evidence. They MUST NOT become new canonical subtype values without a later frozen-contract amendment.

Taxonomy presence means `contract_supported`; it does not authorize network execution.

## 3. Applicability and identity

The initial governed scope is TWSE and TPEx `company_share/common_share` resolved by the existing Security Master.

Binding MUST use resolved market plus exact security code. Company name MUST NOT be a binding fallback. A market/target mismatch MUST fail closed.

Other instrument types are DEFERRED unless a later frozen authority explicitly adds them.

## 4. Conceptual evidence model

Each H1 target evidence MUST be capable of representing:

- `status_type`;
- `status_lifecycle`;
- `published_at` or source record date when supplied;
- `effective_from` and `effective_to` when supplied;
- official reason, conditions and measures when supplied;
- source family, source contract, transport and license authority;
- market and canonical target identity;
- `observed_at`;
- coverage status and covered source scope;
- governed citation identifiers;
- bounded source-native evidence/provenance.

Exact V3 JSON Schema syntax is DEFERRED to H0-G.

## 5. Source-native truth

TWSE and TPEx source fields are not symmetrical. TWT85U and `tpex_cmode`, for example, expose different flags.

Adapters MUST perform source-contract-specific validation and semantic normalization. They MUST preserve source family, contract, native field evidence, transport, timing and license. They MUST NOT invent false field symmetry or drop source-native distinctions required for audit.

## 6. Lifecycle semantics

Allowed conceptual lifecycle values are:

- `reported`;
- `effective`;
- `ended`;
- `unresolved`.

A lifecycle value MUST be supported by official source evidence. Current absence, local date comparison, text similarity, snapshot difference or company-name similarity MUST NOT establish that a status ended, was corrected, or is the same official event.

When official start/end or revision semantics are missing, lifecycle MUST be `unresolved`.

## 7. Result-state semantics

H1 MUST distinguish:

- `available`;
- `no_evidence_in_covered_scope`;
- `partial`;
- `source_failed`;
- `binding_failed`;
- `not_applicable`;
- `unsupported`.

`no_evidence_in_covered_scope` is legal only when the complete governed source scope declared by the result was successfully retrieved, source-contract validated and searched for the exact target.

No row MUST NOT be treated as no status when retrieval failed, binding failed, required route coverage was incomplete, or the subtype was unsupported.

## 8. Coverage semantics

Coverage MUST identify the source snapshot/report date when supplied, retrieval time, covered subtype(s), and whether the declared source scope is complete, partial, unknown, source-failed or unsupported.

If multiple routes are required for the requested subtype set, failure of one route MUST NOT silently disappear. Available evidence MAY be returned as `partial` with failed or uncovered source families listed.

## 9. Source eligibility versus activation

Source role and activation state are separate. A source may be an approved default candidate but remain inactive until its exact license, source contract, deterministic tests and later implementation authorization pass.

At this freeze:

- verified ODGL routes may be `eligible`;
- unresolved license routes remain `inactive`;
- no H1 route becomes `active` merely because this contract is frozen.

The normative route states are in `Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.json`.

## 10. Execution and persistence

H1 acquisition MUST comply with the Phase H product boundary: explicit, target-scoped, data-need-scoped, authorized, execute-once and auditable.

No startup fetch, polling, scheduler, background refresh, hidden market-wide acquisition or status warehouse is authorized.

## 11. Provenance and freeze boundary

Research inputs:

- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Official_Source_Transport_Automation_Authority_Matrix.md`
- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Source_Authority_Matrix.json`

Accepted pre-amendment SHA-256 values:

- Markdown: `566a91f5c7fa1da18dfb85753a19ba6f446973a5dc8040a3ac7996dde0fe31d3`
- JSON: `6a05968b4e2c6bd444bd90942eaffd9f24a55c99b17bd29365211ea3c5cd53f7`

Post-amendment SHA-256 values:

- Markdown: `120cd0278484b429cf618e9041b2bd0eb56edb0e43cee17d00be0af03347b7ef`
- JSON: `6685c236274b662107c0061240f6983e63ce68dee6daa33c1c3e2deef1ef7670`

This file's hash is recorded in `PHASE_H_H0_A_D_FREEZE_MANIFEST.json`.

This document freezes semantics, not V3 schema bytes, runtime adapters or current authority.
