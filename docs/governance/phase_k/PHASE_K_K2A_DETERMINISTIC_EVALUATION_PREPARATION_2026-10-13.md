# Phase K K2-A — Deterministic Evaluation Preparation

**Date:** 2026-10-13
**Status:** Preparation complete; all eight K1 scenarios have deterministic assets; no host evaluation executed
**Principles:** **Prepare common evidence, not common choreography.** Validate interoperability, not behavioral conformity.

## Purpose and boundary

K2-A prepares a small reproducible evaluation root for K1-01 through K1-08. It does not execute ChatGPT, Codex, Hermes, any other host, or a model; it claims no compatibility outcome. It performs no market/source acquisition, production Security Master mutation, or product/runtime contract change. The generated evidence comes from the repository-owned deterministic test executor, explicitly marked `NON_AUTHORITATIVE_TEST_ONLY` with `network_required=false`; it is not production-source evidence.

## Scenario asset map

| K1 | Reused deterministic authority | Status |
|---|---|---|
| K1-01 Surface discovery | `server/unified_mcp/tool_contracts.py::build_tool_contract_snapshot` (canonical six-tool contract) | Available |
| K1-02 Ambiguous identity | `tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json` and the 3333 collision check in `tests/acceptance/test_m8r_06_05_operator_acceptance.py::test_m8r_06_05_localhost_operator_matrix` | Available |
| K1-03 Preview / authorization | `tests/helpers/phase_h_imp_7d_control_package.py::fixture_request` and `fixture_plan`; resolved TPEX:6488, execute-mode, zero network estimate, inspected before source transport | Available |
| K1-04 Stored Result / Handoff | Fresh package from `execute_fixture_package`, then existing Mode C Result/Audit and Local Service read/export APIs | Available |
| K1-05 Stale/currentness | Fresh K2 package regenerated through the repository-owned deterministic raw-source boundary and canonical Local Service / Result V3 / Audit V3 / Handoff path | Available; `current_observation.status=available`, `currentness.status=stale`, timestamps preserved, no trading/recommendation semantics, zero external market/source dispatch |
| K1-06 Partial + source failure | `tests/acceptance/test_m8r_06_05_operator_acceptance.py::test_m8r_06_05_partial_source_failure_and_ui_bindings` using the isolated deterministic test transport | Available; generated package retained in the isolated root and marked test-only |
| K1-07 Unsupported capability | Existing `test_j1_10_financial_statements_fail_closed_through_local_service_and_mcp` request case plus canonical V3 request schema | Available; request is embedded in the existing test rather than a separate fixture file |
| K1-08 Host transport/output classification | Same representative non-trivial generated Result/Audit/Handoff package as K1-04 | Available |

No scenario uses a live substitution. The machine-readable manifest repeats these mappings and records fixture references.

## Isolated root and preparation

Run from a clean checkout with a new disposable directory outside the repository:

```text
python scripts/prepare_phase_k_k2_deterministic_eval.py --root <disposable-evaluation-root>
```

The utility rejects a non-empty root and a root inside the repository. The root contains the generated success, stale, and partial Result/Audit/Handoff packages plus `preparation_manifest.json`. It depends on committed source and test fixtures only; it does not depend on historical Phase-J runtime directories, attempt folders, retained package IDs, Codex bundles, developer usernames, or absolute paths. Delete the disposable root and run the same command to regenerate it.

The K1-04/K1-08 success package uses the existing fixture executor and canonical Mode C and Local Service APIs in-process. K1-05 is freshly finalized on each preparation run from a K2-specific request through the repository-owned deterministic raw-source boundary; no historical Result, Audit, Handoff, or control package is copied. Its package identity is generation-local, while the governed stale semantics are reproducible: source timestamp `2026-09-01T05:30:00Z`, retrieval timestamp `2026-10-08T06:00:00Z`, `currentness.status=stale`, `freshness_assessment=stale_intraday_snapshot`, evidence remains available, and trading/recommendation permissions remain false. K1-06 reuses the isolated deterministic partial-failure transport. All source transports report no external market dispatch. Result, Audit, and Handoff lineage is checked, and `read_result` / `export_ai_handoff` are exercised in both read-only orders without an ordering prerequisite. No Agent host or MCP protocol session is started.

## Preparation manifest and later observation format

`preparation_manifest.json` records only kit version, repository commit, creation time, scenario map, fixture/executor references, generated package and artifact identities/hashes, lineage, the two read-only order checks, network counters, generation command, preparation gaps, and explicit zero host-evaluation/outcome claims. It contains no binary inventory, owner authorization hash, or third-party executable pin. `known_preparation_gaps` is empty after the K1-05 finalized stale package was added.

K2-B may record an observation using this minimal JSON shape; this is a fill-in format, not a schema or adjudicator:

```json
{
  "scenario_id": "K1-01",
  "host_label": "",
  "host_version_observed": "",
  "transport": "",
  "outcome": null,
  "finding_class": null,
  "observed_tools": [],
  "semantic_summary": "",
  "known_limitation": null,
  "evidence_refs": []
}
```

Use the K0 outcome and finding taxonomies. Do not infer PASS/FAIL automatically.

## Acceptance boundary

K2-A is preparation only. Current host evaluation count is **0**; no compatibility outcome is claimed. No public contract, capability, schema, MCP tool, or production runtime is changed. All eight K1 scenarios now have deterministic assets, including the finalized K1-05 stale package. K2-B — Small Multi-Host Pilot & Compatibility Matrix may start only from a merged main that includes this preparation state.
