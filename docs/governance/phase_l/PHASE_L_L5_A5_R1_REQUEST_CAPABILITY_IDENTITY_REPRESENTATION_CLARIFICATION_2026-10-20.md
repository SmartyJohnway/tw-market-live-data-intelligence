# L5-A5-R1 — Request Capability Identity Representation Clarification

Owner authority: `USER_CHAT_2026-10-20_L5_A5_R1_GOVERNANCE_CLARIFICATION`.

The canonical semantic capability identity/namespace is `capability_id`; its Unified Request V3 wire representation is `data_needs[].type`. The value of `request.data_needs[i].type` equals the semantic capability identity value. Thus `type: monthly_revenue` represents capability identity monthly_revenue and `type: material_disclosures` represents material_disclosures. This is an existing representation mapping, not a registry, transformation table, new public field, alias, parser, or migration.

The frozen A1 `data_needs[].capability_id` wording is `HISTORICAL_NOTATION_DEFECT`: historical erroneous field notation, not accepted Unified Request V3 syntax. The original `FROZEN_GOVERNANCE_EXAMPLE_REQUEST_REPRESENTATION_CONTRADICTION` is `RESOLVED_BY_OWNER_GOVERNANCE_CLARIFICATION`.

A1 historical bytes rewritten: NO. Request V3 changed: NO. Public contract changed: NO. Runtime changed: NO. Semantic capability identity changed: NO. The literal capability_id property, alone or in addition to type, continues to fail the closed Request V3 schema. The prior A5 HOLD run and its 23-artifact manifest remain unchanged and correctly record the former fail-closed stop.

Exact entry HEAD/tree: `ade186602cc415bbce8829fc250b842ce725e126` / `1ac63444754c0fd107bb9d9aa4c4257287a15a77`; main/tree: `09d6db51cf242316632bffb7ee96eef88014a039` / `cf3651e3da8dfab26c553d2b3d4a781a5e123e13`. PR #390 entered OPEN/Draft at those exact OIDs. New evidence run: `l5-a5-r1-20261020T151923Z`.

R1 clarification disposition: `L5_A5_R1_REQUEST_CAPABILITY_IDENTITY_REPRESENTATION_CLARIFICATION_PASS`. Representative-family technical acceptance is independently conditioned on all A5 gates; this clarification alone does not accept either family or close GAP-06. A6/A7 and L6–L7 are not authorized; merge is prohibited.

## Completed representative-family acceptance

Final technical disposition: `L5_A5_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE_PASS`. This accepts the candidate proof, not Owner acceptance or production activation. Original A5 HOLD remains unchanged. GAP-06 is technically `CLOSED_BY_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE`: two existing families pass, 72/72 cells adjudicated, zero unresolved and zero DECISION_REQUIRED. No A6 integrated acceptance or A7 exit review is performed.

### Identity graphs and cross-market normalization

- monthly_revenue: semantic capability monthly_revenue → Request V3 data_needs[].type → shared phase_g_official_research_executor → MOPS_MONTHLY_REVENUE_OPEN_DATA → t187ap05_L (TWSE) / t187ap05_O (TPEX) → phase_g_monthly_revenue_operation_evidence.v1 → monthly_revenue_evidence.v1 → canonical Result V3 / Audit V3 / derived handoff.
- material_disclosures: semantic capability material_disclosures → Request V3 data_needs[].type → the same research executor → MOPS_MATERIAL_DISCLOSURE_OPEN_DATA → t187ap04_L (TWSE) / t187ap04_O (TPEX) → phase_g_material_disclosure_operation_evidence.v1 → material_disclosure_evidence.v1 → canonical Result V3 / Audit V3 / derived handoff.

Both market routes bind explicitly to the shared executor; sharing does not merge semantic capability, operation, typed schema or source namespaces. The two market source contracts per family normalize to the same typed schema and equal semantic body after removing market/source/citation provenance. Product-wide N:M remains permitted. The identity inventory is acceptance evidence only, not a runtime family registry.

### Proof details and limits

Four existing payload-fixture cases traverse actual Phase G normalization, shared lineage/citation builders, Result V3, Audit V3 and markdown handoff. The acceptance fixture packages retain canonical operation bytes and matching SHA-256, Result, Audit and handoff for inspection. These are projection-unit fixtures using existing accepted test control identities, not production acquisition or newly qualified production control packages. Existing Phase G Mode C tests separately prove materialization compatibility.

Monthly TWD/thousand units, signed previous-month revenue and null percentages remain source-faithful. Disclosure publication/fact/report dates and bounded description survive projection. Source observation time and bundle citation retrieved_at remain distinct. Actual missing and source-failure scenarios remain different; 51 disclosure-shaped fixture rows produce 50 retained items with partial/truncated status. Unsupported is an existing eligibility/typed status and stale a separate currentness axis; no unsupported acquisition outcome or refresh clock is invented. Handoff exactly follows the shared renderer, preserves state/caveats and rejects invented citations/conclusions at acceptance.

The 36×2 matrix preserves every frozen A1 name/classification and provides explicit applicability, owner, exact evidence paths/symbols, proof type, observations, result and notes. All 72 are applicable, including explicit optional declarations: no guarantee of retaining full raw provider payloads; replay is only from retained platform predecessors and never refetch. No blanket N/A is used.

L1 family modules define no private lifecycle/status/doctor. L2 retention and replay remain existing platform policy; unknown retention fails closed and raw provider replay is not promised. L3 uses existing fetch_once → normalize_source_rows → binding/semantic validation. L4 network, path, secrets, time/item/output/resource/concurrency controls stay with existing platform and selected metadata. The corresponding existing platform suites pass; no competing policy is created.

Catalog, selected Routing, portable Catalog, Quick Guide, Skill, usage guide and limitations pass the accepted A4 publication gates. Publication does not activate routes and guides remain derived. Fifty-nine A5 focused tests reject contract/source/executor/market swaps, target/operation/citation/Audit hash drift, missing dimension proofs, a fake registry, seventh tool, publication contradiction and family-owned retention/security/resource policy. A socket/write-forbidden test executes the entire validator. Existing family/platform suites report 174 passed with exact nodes retained. Required validators pass. Default-ci remains 1,248 passed / 41 failed / four skipped / five deselected; the exact accepted 41-node set is unchanged, candidate-only zero. Those historical failures remain unresolved failures.

Changes are limited to A5 acceptance-only validator/tests, new R1 governance/evidence, and four current front doors. Public schemas, Catalog/Route functional bytes, sources, executors, runtime and dependencies are unchanged. Historical A1–A4 manifest identities and original A5 HOLD are preserved. Provider requests, live acquisition and production mutations: zero. External socket attempts: NOT_MEASURED (the focused socket guard is process/test-scoped, not OS-wide accounting).

Stop boundary: update existing PR #390 and mark Ready only on full PASS; do not merge, authorize A6/A7, start L6/L7, or mutate SMARTY. L5 remains STARTED; A0–A4 remain Owner-accepted/merged; A5 Owner acceptance is pending.
