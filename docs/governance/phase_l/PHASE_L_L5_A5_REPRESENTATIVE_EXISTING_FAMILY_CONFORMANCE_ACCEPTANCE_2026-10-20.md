# L5-A5 — Representative Existing-Family Conformance Acceptance

Disposition: `L5_A5_EXISTING_FAMILY_CONFORMANCE_GAP_REQUIRES_OWNER_DECISION`. **HOLD / NOT MERGEABLE BY GOVERNANCE**. Owner authority: `USER_CHAT_2026-10-20_PHASE_L_L5_A5_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE_AUTHORIZATION`.

Exact entry main `09d6db51cf242316632bffb7ee96eef88014a039`, tree `cf3651e3da8dfab26c553d2b3d4a781a5e123e13`; six required milestone ancestry checks passed. The branch `phase-l/l5-a5-representative-existing-family-conformance` began clean from that exact entry. Evidence run: `l5-a5-20261020T143928Z`.

## Blocking frozen-input discrepancy

The A1 frozen examples and A5 sections 7–8 require `data_needs[].capability_id = monthly_revenue/material_disclosures`. The current frozen Unified Request V3 schema instead requires `data_needs[].type` and `priority`; its data-need objects set `additionalProperties: false`. `capability_id` is not a public Request field. The current capability identities and operation-evidence `capability_id` do not make that field legal in the public Request.

Exact evidence: `acceptance_runs/l5-a1-20261018T140202Z/existing_family_conformance_examples.json` lines 25 and 55; `schemas/unified_market_evidence_request.v3.schema.json` lines 58, 91–94, and 133. `server/services/unified_contract_versions.py::resolve_request_schema` selects the exact declared frozen schema.

The bounded offline Draft7 schema probe tests both existing families. Current `type` requests pass; literal `capability_id` requests fail; including both fields also fails the closed object schema. All six diagnostic expectations are reproduced in `request_representation_probe.json`. This does not identify a product schema bug or authorize a new alias.

A5 cannot truthfully claim the literal frozen example representation conforms. Changing Request V3, rewriting A1 historical examples, or silently interpreting the literal field as an alias would cross the authorization boundary. Owner must separately clarify the governance representation of public `type` versus capability identity, or authorize a public-contract change outside this tranche. No choice is made here.

## Bounded acceptance status

The two mandatory representatives remain `monthly_revenue` and `material_disclosures`; their existing identity graphs are preserved from A1. No family/capability/source/executor/schema/tool is added. The 36 frozen classifications are inventoried for both families (72 cells), with **0 conformance cells adjudicated and 72 unresolved** after the stop condition. No cell receives a fabricated PASS or N/A. GAP-06 remains `OPEN_OWNER_DECISION_REQUIRED`; neither family is accepted by A5.

Cross-market normalization, semantic proof, lineage/citation, Result/Audit/handoff, L1–L4 inheritance, publication, full negative-mutation acceptance, required acceptance validators, and default-ci were not run after the stop condition. Their evidence entries explicitly record NOT_RUN_BLOCKED. Existing family test expectations are unchanged. The six diagnostic schema cases are not a substitute for A5 acceptance tests. No assertion about a new candidate default-ci failure set is made; the accepted historical baseline remains 41 failed nodes.

## Integrity and stop boundary

The six requested A1–A4 manifest identities recompute correctly, and their manifest bytes equal the exact entry base. A1's 36 dimensions, zero DECISION_REQUIRED classifications, prohibited universal family registry, and T1–T12 version matrix remain unchanged. Historical source members are not compared as if later current bytes were their original snapshots.

Only this A5 governance/evidence package changes. Runtime, Catalog, Routing, executors, sources, schemas, public contracts, tests, dependencies, and four current front doors remain unchanged. Provider requests, live acquisition, and production state mutations are zero; external socket attempts are NOT_MEASURED. L5 remains STARTED, A0–A4 Owner-accepted and merged. A5 Owner acceptance is pending. A6 integrated acceptance, A7 exit review, L6–L7, and SMARTY mutations are not authorized.

The review handoff is a bounded commit and Draft PR clearly marked HOLD; merge is prohibited.
