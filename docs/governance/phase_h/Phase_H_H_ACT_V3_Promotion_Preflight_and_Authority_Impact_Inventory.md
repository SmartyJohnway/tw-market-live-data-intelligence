# Phase H — H-ACT-V3 Promotion Preflight + Exact Authority Impact Inventory

Status: **PREFLIGHT PASS — READY FOR OWNER PROMOTION AUTHORIZATION**  
Baseline main: `d2e2da1c42de3f1790dcc50c7bd1fa3093f15cce`  
Date: 2026-09-23

This preflight is deliberately non-mutating. It does **not** promote V3, change preferred request/result authority, activate another source route, execute external network access, or publish a release.

The machine-readable companion is:

`docs/governance/phase_h/PHASE_H_H_ACT_V3_PROMOTION_PREFLIGHT_AND_AUTHORITY_IMPACT_INVENTORY.json`

## 1. Executive conclusion

H-ACT-V3 has no newly discovered source-authority, schema, bounded-live, Result/Audit, authorization, portability, or scope blocker.

The critical-path prerequisites are present:

- H-IMP-7D: PASS and merged.
- H-ACT-H1: PASS and merged.
- H-ACC-7L / H0H-E2E-LIVE-001: PASS and merged.
- Phase H active source set: exactly one route, `H1-TPEX-ATTENTION-OPENAPI`.
- Every currently active Phase H route has route-level live and rollback evidence.
- Frozen Request V3 / Result V3 / Audit V3 contracts already exist and passed deterministic plus live product projection.

The remaining entry criterion is the independent Owner approval required by H-ACT-V3. Promotion is **not** authorized by this preflight.

The implementation is not a two-string change. Current authority is intentionally split across the V3 Workbench path, the V2 Local Service/MCP product surface, Mode C V2 defaults, the Watchlist builder, and the portable Agent Skill. Those surfaces must move atomically or fail closed.

## 2. Current pre-promotion truth

At the baseline:

- preferred Request: `unified_market_evidence_request.v2`;
- emitted Result authority: `unified_market_evidence_result.v2`;
- V3 runtime state: `selected_routes_active_v2_preferred`;
- Phase H active source count: `1`;
- active Phase H route: `H1-TPEX-ATTENTION-OPENAPI`;
- H1 coverage remains partial: attention only;
- H2 and H3 remain inactive / blocked / plan-only according to V3 routing truth;
- MCP surface remains exactly six tools.

The V3 planning pair already inherits existing Phase G executable routes and exposes the exact H1 selected route. It also retains blocked/plan-only H2/H3 truth.

## 3. Required H-ACT-V3 acceptance evidence

All sixteen H-ACT-V3 requirement IDs have pre-promotion evidence. They are not all automatically final after the authority switch.

| Requirement | Current evidence | Promotion-candidate action |
|---|---|---|
| H0H-V3-001 | PASS via H-IMP-0 and H-IMP-7D V2 regression | rerun V1/V2 compatibility after V3 becomes preferred |
| H0H-V3-003 | PASS via passive/inactive V3 preview and H-ACT-H1 routing | rerun blocked/plan-only V3 cases |
| H0H-H4-001 | PASS in H-IMP-1 | rerun promoted Result/Handoff guard path |
| H0H-H4-004 | PASS in H-IMP-1 | rerun failure/coverage-incomplete matrix |
| H0H-OUT-001 | PASS in H-IMP-6 + live Result V3 | validate preferred Result V3 |
| H0H-OUT-002 | PASS in H-IMP-6 + live Audit V3 | validate preferred Audit V3 |
| H0H-OUT-004 | PASS in H-IMP-6 + live handoff | validate preferred AI handoff |
| H0H-NET-001 | PASS in H-IMP-7D S13 | rerun startup zero-network guard |
| H0H-MCP-001 | PASS, six tools | prove still exactly six after V3 input expansion |
| H0H-E2E-001 | PASS in H-IMP-7D | rerun promoted deterministic E2E |
| H0H-E2E-002 | PASS in H-IMP-7D | prove inactive V3 routes fail closed and V2 remains usable |
| H0H-E2E-LIVE-001 | PASS in H-ACC-7L | live evidence remains valid unless active-route semantics change |
| H0H-AUTH-001 | PASS in H-IMP-7D + H-ACC-7L | rerun V3 MCP/Workbench authorize + execute-once |
| H0H-PORT-001 | PASS in H-IMP-7D | rerun fresh install in promoted state |
| H0H-ROLL-002 | rollback model PASS in H-IMP-7D | **actual V3-preferred → V2-preferred rehearsal required** |
| H0H-SCOPE-001 | PASS | rerun changed-file and forbidden-behavior scan |

The most important distinction is H0H-ROLL-002: the existing fixture simulation proves the rollback model, but H-ACT-V3 closure must prove rollback against the actual promotion candidate.

## 4. Exact authority impact

### 4.1 Catalog and F3 validation

`docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json` is the current V3 projection but still records V2 as preferred and V3 as future/selected-route authority.

Promotion must update its current-state fields truthfully:

- `preferred_request_schema_version`;
- `emitted_result_schema_version`;
- `v3_runtime_authority_status`;
- `phase_h_contract.runtime_authority`;
- `phase_h_contract.preferred_runtime_request_schema_version`;
- any current `known_limitations` text saying V2 is preferred;
- the `future_candidate_*` fields must no longer misleadingly describe the now-current V3 authority.

The exact promoted-state vocabulary must be frozen during H-ACT-V3 implementation. Do not use a vague generic `active` value.

`scripts/m8r_05a_f3/request_intake.py` currently treats a V3 catalog as valid only when it says V2 preferred / Result V2 and the V3 runtime status is either inactive or `selected_routes_active_v2_preferred`. It must accept the single promoted state while keeping V2 Catalog validation unchanged.

`scripts/validate_phase_h_v3_contracts.py` is intentionally current-state mutable, unlike the H0-G freeze manifest. Its V2-preferred assertions must be realigned, while the frozen V3 schema hashes remain protected.

### 4.2 Preferred Request and planner authority

`server/services/unified_contract_versions.py` currently defines V3 for passive dispatch but leaves `EXECUTION_REQUEST_SCHEMA_VERSIONS` at V1/V2. Promotion must add V3 execution authority and should become the single source for preferred Request/Result version constants so other modules do not carry independent strings.

`server/services/unified_mode_a.py` has a backward-compatible canonical preload seam pinned to V2. Explicit version dispatch already works and must remain. Only the current preferred preload seam changes.

`scripts/m8r_06_02_mode_b1_preview.py` defaults `load_planning_authorities()` to V2. Explicit V3 requests already select V3 correctly. After promotion, callers that rely on the default must receive the current preferred V3 authority.

### 4.3 Local Service and MCP

This is the highest-risk split-brain area.

`server/services/unified_local_service.py` still loads:

- Catalog V2;
- Routing Matrix V2.

Therefore `market_describe_capabilities` currently describes the V2 product even though the explicit Workbench V3 path can already execute the selected H1 route. Promotion must move Local Service current authority to V3 Catalog/Route.

`server/unified_mcp/tool_contracts.py` currently:

- sets `PREFERRED_REQUEST_SCHEMA_VERSION = ...v2`;
- builds passive validate/preview schemas with V1/V2/V3;
- builds `market_fetch_evidence` with V1/V2 only.

H-ACT-V3 must keep the exact same six tool names, but expand the existing action tool's request envelope to V3 and make V3 the canonical preferred schema.

`server/services/unified_local_operator_action.py` has a second V3 barrier and explicitly asks Mode C for `output_schema_version="v2"`. Both are pre-promotion controls and must be replaced by the promoted policy.

`server/services/unified_mode_b2.py` has two transitional controls:

1. Workbench V3 authorization is narrowed to the H-ACT-H1 TPEx-attention route.
2. Local-operator V3 authorization is blanket-denied.

Those controls were correct for P4/P5. They cannot remain the product-wide policy at P6.

The promoted rule should be: **V3 execution is governed by V3 Catalog/Route truth and normal authorization/consumption controls.** Existing inherited resolved V3 routes and the exact active H1 route may execute when explicitly requested and authorized. Inactive, blocked, plan-only or unsupported H2/H3 routes remain non-executable. Promotion is not a source activation mechanism.

## 5. Result / Audit / handoff authority

`server/services/unified_mode_c.py` currently defaults Result/Audit/handoff materialization to V2.

H-ACC-7L produced valid live Result V3/Audit V3 by explicitly requesting V3 inside the acceptance runner. The public Workbench/MCP read routes do not expose an output-version switch; they inherit the server default.

Therefore H-ACT-V3 must move the **server-owned default** to V3.

The existing `_persisted_output_version()` behavior is valuable and should remain: if a historical package already contains V1, V2 or V3 outputs, read/verify that persisted version rather than rematerializing it as another version. This is the core byte-preserving compatibility mechanism.

No caller-controlled arbitrary version selection should be added to the public MCP or Workbench route just to implement promotion.

## 6. Persistent Watchlist primary UI path

The Workbench's normal builder path is not V3-ready even though the advanced JSON path is.

`frontend/unified-workbench/watchlist-workbench.js` hardcodes:

`watchlist_evidence_selection_request.v2`

`server/services/watchlist_evidence_composer.py` supports only selection v1/v2, reads Catalog V2 for bounds, and emits Unified Request V1/V2.

Once Local Service begins describing V3 capabilities, the capability builder can display Phase H capabilities that the v2 selection schema cannot legally compose. This would be a real product inconsistency.

The safe implementation is additive:

- add `watchlist_evidence_selection_request.v3.schema.json`;
- add a composer v3 mapping to Unified Request V3;
- use the V3 Catalog for v3 selection bounds/capability truth;
- make the UI primary builder use selection v3 after promotion;
- retain v1/v2 selection/request compatibility rather than rewriting old schemas.

H4 remains derived evidence and must not become a selectable Request data need.

## 7. Portable Agent Skill and current user-facing authority

Promotion must include the portable AI surface. Today:

- `skills/tw-market-evidence-agent/SKILL.md` says Request V2 is preferred;
- `scripts/generate_portable_catalog.py` generates from Catalog V2;
- `validate_portable_catalog_sync.py` deep-syncs against that V2 source;
- `validate_runtime_skill_guide_sync.py` explicitly requires V2 current authority;
- `skills/.../scripts/validate_skill.py` requires the V2 preferred schema text;
- the portable JSON and Quick Guide are V2 projections.

If runtime becomes V3 preferred while the Skill remains V2-current, the installation ceases to be truthfully portable for an AI agent.

These files therefore belong in the same promotion change set, not a later documentation cleanup.

## 8. Historical authority that must not be rewritten

The following are evidence of what was true when earlier gates closed, not current-state configuration to edit:

- H0-G schema freeze manifest;
- H-IMP-0 / H-IMP-1 / H-IMP-6 acceptance manifests;
- H-IMP-7D deterministic E2E ledger;
- H-ACT-H1 acceptance ledger;
- H-ACC-7L live E2E ledger;
- Catalog V2 and Routing Matrix V2;
- Request/Result V1 and V2 schemas and historical packages.

Tests that currently mix historical assertions with current runtime assertions must be separated instead of changing the historical evidence.

## 9. Promotion design decisions fixed by this preflight

1. **V3 promotion is product-wide preferred-contract promotion.** It is not another TPEx-attention exception.
2. **Promotion does not activate another source.** Phase H active-source count remains one unless a separate H-ACT-Hx gate later changes it.
3. **Six MCP tool names remain frozen.** V3 capability is added to the existing safe tools.
4. **Preferred output is server-owned.** New unmaterialized packages default to V3; historical persisted packages keep their stored version.
5. **V2 remains compatibility and rollback authority.** It stops being preferred, but accepted V1/V2 requests and historical V1/V2 packages remain supported.
6. **Partial H1 remains partial.** V3 preferred does not make disposition/suspension/resumption/changed-trading magically covered.

## 10. Promotion candidate acceptance plan

After explicit Owner H-ACT-V3 authorization, implementation should be one coordinated authority realignment. Before merge it must prove:

- V1 validation/planning/execution compatibility;
- V2 validation/planning/execution compatibility;
- preferred V3 validation/planning/authorization/execute-once;
- V3 MCP `market_fetch_evidence` for inherited resolved Phase G routes and active H1;
- fail-closed inactive/blocked/plan-only V3 routes;
- Result V3, Audit V3 and AI handoff;
- source-failed, binding-failed, partial and legal no-evidence semantics;
- exact six MCP tools;
- zero startup network;
- fresh-install behavior without optional providers;
- Watchlist primary builder emits valid V3;
- portable Skill/catalog/guide is V3-current and synchronized;
- historical V1/V2/V3 artifacts remain hash-identical;
- actual V3-preferred → V2-preferred rollback rehearsal;
- rollback restores current capability/MCP preferred-version truth;
- no scheduler, polling, background refresh, warehouse, backfill, TA, screening, ranking, trading, identity fork or seventh MCP tool.

## 11. Preflight verdict

```text
H-ACT-V3 PROMOTION PREFLIGHT
PASS

Technical prerequisites:
SATISFIED

Required bounded-live product evidence:
SATISFIED

Current active Phase H routes covered by live evidence:
YES — 1 / 1

New source activation required:
NO

Frozen V3 schema change required:
NO

Runtime/current-authority realignment required:
YES

Owner promotion authorization:
NOT YET GRANTED

Promotion performed:
NO

Next state:
READY FOR OWNER H-ACT-V3 PROMOTION AUTHORIZATION
```

The promotion should not begin until that independent Owner authorization is given.
