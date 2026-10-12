# Phase K K2-A — Deterministic Evaluation Preparation

**Date:** 2026-10-13
**Status:** Preparation candidate; no host evaluation executed
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
| K1-05 Stale/currentness | `tests/fixtures/m8r_03c/snapshot_stale_observations.json` (copied into the evaluation root) | **GAP:** this is a stale observation input, but no reusable finalized Unified V3 Result/Audit/Handoff fixture currently projects it as stale while preserving evidence availability. No substitute is generated. |
| K1-06 Partial + source failure | `tests/acceptance/test_m8r_06_05_operator_acceptance.py::test_m8r_06_05_partial_source_failure_and_ui_bindings` using the isolated deterministic test transport | Available; generated package retained in the isolated root and marked test-only |
| K1-07 Unsupported capability | Existing `test_j1_10_financial_statements_fail_closed_through_local_service_and_mcp` request case plus canonical V3 request schema | Available; request is embedded in the existing test rather than a separate fixture file |
| K1-08 Host transport/output classification | Same representative non-trivial generated Result/Audit/Handoff package as K1-04 | Available |

No scenario uses a live substitution. The machine-readable manifest repeats these mappings and records fixture references.

## Isolated root and preparation

Run from a clean checkout with a new disposable directory outside the repository:

```text
python scripts/prepare_phase_k_k2_deterministic_eval.py --root <disposable-evaluation-root>
```

The utility rejects a non-empty root and a root inside the repository. The root contains `packages/<control_package_id>/` with existing governed control/receipt/evidence/Result/Audit artifacts, `handoff.json`, and `preparation_manifest.json`. It depends on committed source and test fixtures only; it does not depend on historical Phase-J runtime directories, attempt folders, retained package IDs, Codex bundles, developer usernames, or absolute paths. Delete the disposable root and run the same command to regenerate it.

The successful K1-04/K1-08 package uses the existing fixture executor and canonical Mode C and Local Service APIs in-process. K1-06 reuses the repository's isolated M8R deterministic test transport, with a test-only Security Master beneath the evaluation root; it checks that one evidence family succeeds while the official EOD family remains visibly failed in Result and Handoff. The transport is explicitly deterministic test transport and reports `external_market_network_executed=false`; it is not live or production evidence. A parent-process socket guard blocks external connections. Result, Audit, and Handoff are checked for continuous `result_id` and audit identity lineage. `read_result` and `export_ai_handoff` are each exercised in both read-only orders; the utility enforces neither order as a prerequisite. No Agent host or MCP protocol session is started.

## Preparation manifest and later observation format

`preparation_manifest.json` records only kit version, repository commit, creation time, scenario map, fixture/executor references, generated package and artifact identities/hashes, lineage, the two read-only order checks, network counters, generation command, gaps, and explicit zero host-evaluation/outcome claims. It contains no binary inventory, owner authorization hash, or third-party executable pin. K1-05 remains an explicit gap; the stale input is included for later fixture preparation, without being presented as a canonical Result.

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

K2-A is preparation only. Current host evaluation count is **0**; no compatibility outcome is claimed. No public contract, capability, schema, MCP tool, or production runtime is changed. K2-B — Small Multi-Host Pilot & Compatibility Matrix remains NOT STARTED.
