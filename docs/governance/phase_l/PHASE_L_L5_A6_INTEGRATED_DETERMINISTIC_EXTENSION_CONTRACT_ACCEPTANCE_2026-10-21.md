# Phase L5-A6 — Integrated Deterministic Extension-Contract Acceptance

Authority: `USER_CHAT_2026-10-21_PHASE_L_L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_AUTHORIZATION`.
Exact entry main/HEAD: `928de0f930b0733e188ef3c873f994ce9e8a69d3`; tree:
`320fa08120fe159bf4acead6267875cd6917b298`. Fetch and all five specified A5
milestone ancestry checks passed. Branch:
`phase-l/l5-a6-integrated-deterministic-extension-contract-acceptance` began clean.
Run: `l5-a6-20261021T031032Z`.

Technical disposition:
`L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_PASS`.
**Owner acceptance remains PENDING. L5 remains STARTED. A7, L6-L7 and Phase M are NOT AUTHORIZED.**

## Architecture and existing execution seam

Frozen L0 and accepted A1-A5 remain authoritative. The source inventory → source
contract → capability → schema → adapter → normalization → timing/currentness →
Result → tests → Skill/guide → acceptance flow remains intact. This tranche
connects those existing boundaries; it creates no family, registry, capability,
discovery mechanism, plugin framework or public contract.

The primary harness uses the real `server.unified_mcp.server.dispatch_safe_tool`,
`UnifiedLocalServiceClient`, tool schemas and FastAPI routes through ASGI. Each
trace calls describe → validate → preview → `market_fetch_evidence` → read Result
→ export handoff. All six existing public tools are observed.

The seam gate passed by actual execution. Existing Phase J acceptance precedents
(`tests/helpers/phase_j_closure_r1_transport.py`, its server bootstrap, and
`phase_j_j2_r1_transport.py`) already install raw transport in a test child and
then invoke unchanged `m8r_06_03_execute_once.main`. The A6 acceptance-only helper
uses that pattern: test child bootstrap installs only
`m8r_06_03_production_adapter.urlopen`. It returns existing Phase G fixture CSV
bytes or a bounded fixture transport error. It does not substitute the planner,
registry, selected adapter/executor, operation/typed evidence, Result, Audit,
citations or renderer. The real child validates the control package, consumes
the authorization once and executes the production registry. No runtime hook
was added. This test bootstrap is not a production executable-selection feature.

Other substitutions are limited to the accepted fixture Security Master
bootstrap, in-process ASGI and temporary installation/control roots. The
Security Master release is qualified and activated only under a temporary test
installation. No installation-local production state is changed.

## Integrated traces and graphs

| Trace | Target | Source contracts | Observed Result |
|---|---|---|---|
| A6-T1 | TWSE:2330 | t187ap05_L / t187ap04_L | full_success |
| A6-T2 | TPEX:6488 | t187ap05_O / t187ap04_O | full_success |
| A6-T3 | TWSE:2330 | monthly success; both material-disclosure transports fail | partially_failed |

Both required families retain separate semantic capability, Request `type`,
operation/typed contract and source identities while sharing
`phase_g_official_research_executor`. TWSE/TPEx source contracts normalize into
the same accepted typed contracts. No third family is introduced.

Each graph contains the required S01-S25 nodes and 24 explicit connecting edges:
75 observed stages / 72 verified edges across three graphs. Nodes retain actual
values and owning code seams; edges retain request, target, capability and
operation identities with source artifacts and verification rules. Trace files
contain the actual six responses, control/retained artifacts, disk byte hashes,
transport receipts and operational events. This is not a sum of validator PASSes.

Checks bind the public Request to the preview/control request, actual selected
operations, authorization scope and single-use ticket; market/target/executor
to operation and typed evidence; actual retained bytes to Audit and citation
hashes; source contracts to normalized families; independently recomputed Result
and Audit hashes to read/export envelopes; handoff citations to the Audit map.
The full handoff is checked against read-result markdown and the actual shared
renderer. Only the renderer's builder-owned currentness map display order is
restored after canonical JSON key sorting; values are unchanged.

## Dimension ledger, determinism and containment

The frozen 36 A1 dimensions are accounted one-for-one, with no new classification
or A5 72-cell matrix. The ledger assigns `TRACE_PROVEN`,
`TRACE_PLUS_ACCEPTED_GATE`, `PLATFORM_INHERITED_ACCEPTED_GATE`, or
`DERIVED_PUBLICATION_GATE`; each row records trace stages, exact authority,
delegated gates and evidence files. Result: 36/36 accounted, zero unresolved,
zero `DECISION_REQUIRED`. Accepted family Owner decisions are inherited; this
technical ledger does not grant A6 Owner acceptance.

T1 and T2 each execute twice in separate temporary roots. Plan operations,
transport/source selection, full normalized family semantics, semantic operation
hashes, the complete Result semantic body/hash, Audit operation lineage and full
handoff text compare equal. The evidence explicitly lists each excluded
retrieval/execution clock and its dependent Result/Audit ID or artifact hash.
Original integrity hashes are independently verified before those run-local
values are replaced for semantic comparison. Source report dates, publication
timestamps, units, nulls, values, states, caveats and citations remain compared.
No blanket timestamp/ID/hash stripping is used.

T3 observes `source_failed` with `all_governed_transports_failed` for material
disclosures while revenue remains available with value 100. The actual Result
is `partially_failed`. Failure evidence retains its provenance; no unavailable
value is changed to zero or converted into healthy missing evidence. Handoff
retains the failure and caveat and invents no citation or conclusion.

Focused coverage includes 26 trace/authority mutation cases plus public-path
refusals for `financial_statements`, a literal `capability_id` property, an extra
`capability_id` property and a request changed after preview. It also includes
an intentional child socket-guard rejection. No public alias is added:
semantic `capability_id` continues to be represented by Request V3
`data_needs[].type`.

## Publication and platform inheritance

Current Catalog/selected Routing, portable Catalog, Quick Guide, Skill, usage
guide and limitations pass the accepted A4 publication gate and both independent
sync gates. Describe reports Request/Result V3 preferences and distinguishes
contract support from executability. Publication remains derived and cannot
activate a route.

- L1: actual source/adapter duration events and child completion share one fetch
  trace ID; Request/operation/authorization identity is retained in the package.
  No separate family-owned lifecycle or operational truth is created.
- L2: actual retained operation/Result/Audit artifacts remain platform-governed;
  accepted replay/retention tests distinguish read/replay from refetch and
  preserve fail-closed unknown-artifact classification. No migration policy is
  invented or exercised.
- L3: fixture raw HTTP bytes pass through real transport → source-contract →
  semantic validation. Both successful and failed acquisition states are
  observed; accepted drift protections are inherited.
- L4: actual authorization/claim/fixed child and contained temporary paths are
  used. Accepted path, hostile-content/secret, numeric/resource and concurrency
  gates remain required. No family-owned platform policy is introduced.

## Validation and historical integrity

Final focused tests: **35 passed**. Existing integration, safe MCP surface,
Phase G source/routing/production-adapter/Result/Mode C, A5 and delegated L1-L4
suites: **232 passed**. The first existing-suite attempt lacked a test Security
Master installation and returned HTTP 503 for one J2 schema-refusal test. That
raw failure remains in `existing-uninitialized.*`; rerunning the unchanged suite
with the accepted isolated fixture-release setup passed. No historical test was
weakened or deselected.

All **16 required deterministic gates PASS**, including the new integrated
validator, A2-A5 gates, dependency/environment checks, compileall and diff check.
Default-ci remains **1248 passed / 41 failed / 4 skipped / 5 deselected**. Exact
node equality against the accepted A5 historical set is TRUE; candidate-only
failures are zero. Initial extraction from A0 included one assertion diagnostic
suffix rather than a node ID; the diagnostic is preserved and the accepted A5
normalization is explicit. The 41 failures remain unresolved and non-passing.
The final candidate rerun finished at `2026-10-21T04:24:11Z` with that same exact
failure set. A preceding parent-only UTF-8 attempt could not decode child output;
its harness error remains in `default-ci-final-encoding-error.log` and is not an
acceptance result. The final run used inherited `PYTHONUTF8=1` and
`PYTHONIOENCODING=utf-8`, without modifying the profile runner or tests.

Historical A0/A0-R1/A1/A1-R1/A2/A2-R1/A3/A4/A4-R1/A4-R2/A5-HOLD/A5-R1 manifest canonical
identities and entry bytes are verified unchanged. Later current front-door
bytes are not represented as historical member matches. Current A3 Owner
acceptance records independent final-candidate 30/30 verification and explicitly
states that no A3-R1 reconciliation is required; that accepted gate truth is
preserved without re-adjudication.
A1's 36 dimensions, T1-T12, Request/Result/Audit schemas, typed/source contracts,
Catalog/Route authorities, production adapter/executor and dependencies are
unchanged; no version transition is invoked.

Provider requests: 0. Live acquisition: 0. Production-state mutations: 0.
Unexpected external socket attempts in primary traces/repeats: 0. Instrumentation
covers parent connect/connect_ex/getaddrinfo (loopback permitted for Windows
asyncio's self-pipe) and child Python socket audit events; it is not OS-wide
network observation. The intentional blocked guard self-test is separate.

## Review boundary

Only acceptance validator/helpers/tests, this governance/evidence package and
four current front doors change. Runtime/product/schema/Catalog/routing/source/
executor/dependency changes are zero. A1-A5 evidence is not rewritten. Candidate
commit and review PR are authorized; merge, auto-merge, A7 and L6-L7 are not.
Stop at PR handoff with **Owner acceptance PENDING**.
