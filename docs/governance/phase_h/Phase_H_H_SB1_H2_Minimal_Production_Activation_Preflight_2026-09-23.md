# Phase H H-SB1 — H2 Minimal Production Activation Preflight

Status: **PREFLIGHT PASS / IMPLEMENTATION READY / SOURCE ACTIVATION NOT YET EFFECTIVE**

Date: 2026-09-23  
Project: tw-market-live-data-intelligence  
Baseline: e033302fa78b81b7644f0de059d20c1c91321d31

## 1. Goal

Activate the smallest real H2 production slice needed for the Phase H interpretation-safety belt without expanding H2 into a corporate-action database.

Selected market:

\`\`\`text
TPEX
\`\`\`

Selected paired source lanes:

\`\`\`text
H2-TPEX-EXRIGHT-PRE-OPENAPI
H2-TPEX-EXRIGHT-FINAL-OPENAPI
\`\`\`

Capability:

\`\`\`text
corporate_action_context
\`\`\`

## 2. Why this pair

The frozen H0/H-SB0 authorities already identify this pair as the safest first H2 activation candidate.

Both routes are:

- official TPEx sources;
- structured JSON OpenAPI;
- ODGL-authorized;
- credential-free;
- portable;
- already represented in frozen source authority;
- already implemented as accepted dormant normalizers.

Together they preserve the critical H2 distinction:

\`\`\`text
preannouncement / scheduled context
!=
official final reference calculation
\`\`\`

## 3. Existing implementation readiness

H-IMP-3 is Owner-accepted complete.

Dormant implementation already exists for:

\`\`\`text
normalize_tpex_exright_prepost
normalize_tpex_exright_daily
assemble_corporate_action_context
\`\`\`

Accepted semantics already prove:

- exact market/security-code binding;
- name never binds;
- preannouncement/final stage separation;
- blank / zero / not-announced / unavailable distinction;
- deterministic event classification;
- ambiguous event classification fails closed;
- truthful partial coverage;
- uncovered subtypes remain visible;
- revision uncertainty preserved;
- source-contract drift fails closed;
- H2→H4 deterministic safety behavior;
- zero-network component determinism.

Therefore H-SB1 MUST NOT redesign the H2 schema or semantic contract.

## 4. Remaining work

The gap is runtime wiring and route activation evidence.

Required implementation:

1. add one governed production executor for \`corporate_action_context + TPEX\`;
2. the executor performs exactly two bounded official calls at most:
   - tpex_exright_prepost;
   - tpex_exright_daily;
3. normalize each source independently using the accepted dormant normalizers;
4. assemble one target-scoped H2 evidence object;
5. persist only normalized target evidence plus source-attempt governance;
6. no raw full-market payload retention;
7. register the executor in existing 05B-03 production registry;
8. keep the same explicit authorization / execute-once controls;
9. no batch/full-market accumulation semantics;
10. no new MCP tool.

## 5. Proposed runtime identity

Recommended executor identity:

\`\`\`text
phase_h_h2_tpex_exright_executor
\`\`\`

Route:

\`\`\`text
capability = corporate_action_context
market     = TPEX
network    = true
approval   = required
max result items = 1
output     = corporate_action_context_evidence.v1
\`\`\`

## 6. Call bound

For one exact authorized target:

\`\`\`text
maximum official source calls = 2
retry storm                   = prohibited
fallback to unofficial source = prohibited
\`\`\`

A single source failure must remain visible in H2 coverage/attempt evidence.

No-row from one source must not erase uncovered scope or source state.

## 7. Coverage rule

Even after this pair activates, H2 declared scope remains broader than ex-right/ex-dividend.

Therefore activation MUST NOT imply:

\`\`\`text
complete corporate-action coverage
\`\`\`

Known uncovered/manual/source-gap families remain visible, including:

- capital-reduction automation;
- par-value change;
- split / reverse split / consolidation;
- unresolved revision/cancellation completeness.

Accordingly H4 may still emit \`coverage_incomplete\` for windows where uncovered relevant subtypes prevent a complete conclusion.

This is expected safe behavior.

## 8. Activation sequence

\`\`\`text
H-SB1-A
production executor + registry wiring
ROUTE REMAINS INACTIVE

H-SB1-B
network-free unit/integration acceptance

H-SB1-C
Owner-authorized bounded-live probe
exact target
max two source calls

H-SB1-D
rollback rehearsal

H-SB1-E
Owner activation approval

H-SB1-F
Catalog / Routing / Skill / capability docs
updated to exact active subset
\`\`\`

No step implies the next step.

## 9. Bounded-live acceptance

The live probe must record:

- exact target;
- exact endpoint URLs / source IDs;
- request timestamp;
- HTTP outcome;
- row binding result;
- source schema/field validation;
- normalized pre/final stage result;
- coverage set;
- citation IDs;
- call count;
- no raw-payload retention;
- Result/Audit projection behavior;
- rollback evidence.

At least one of these outcomes is acceptable if truthful:

\`\`\`text
event available
no_evidence_in_covered_scope
partial
source_failed
binding_failed
\`\`\`

A no-event-like result is valid only for the actually covered source slice.

## 10. Required regression proof

Before activation:

- focused H2 tests PASS;
- production-adapter tests PASS;
- H4 tests PASS;
- V3 preview/authorization tests PASS;
- Default CI PASS;
- Full Non-Network introduces no new unexplained failures;
- V1/V2 compatibility unchanged;
- exactly six MCP tools;
- H3 remains blocked;
- Phase I remains not started.

## 11. Rollback

Rollback is:

\`\`\`text
active
→ inactive / plan-only
\`\`\`

while preserving already written governed evidence.

Rollback triggers include:

- source schema drift;
- changed binding semantics;
- changed no-row semantics;
- source/license authority change;
- evidence schema failure;
- unexplained regression.

## 12. Preflight decision

\`\`\`text
H2 semantic redesign required        = NO
H2 dormant implementation ready      = YES
TPEx pre route source authority       = READY
TPEx final route source authority     = READY
production executor exists            = NO
bounded-live acceptance               = NOT YET RUN
route activation                      = NOT YET EFFECTIVE

H-SB1 implementation                  = READY
\`\`\`

This preflight authorizes no silent source activation by itself.
