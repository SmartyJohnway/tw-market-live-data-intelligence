# L7-A0 — CI / Release Current-State Inventory & Governance Contract

Status: **TECHNICAL INVENTORY / GOVERNANCE CONTRACT COMPLETE; OWNER ACCEPTANCE PENDING**.
Technical disposition: `L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_FROZEN`.
Review completed on 2026-10-24 Asia/Taipei; authorization date retained in filename.

Authority: `USER_CHAT_2026-10-23_PHASE_L_L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_AUTHORIZATION`.
Exact entry is PR #407 merge `125188604126bcdbfcfea0f6421eae6a160e9085`, tree
`604c2e973a443c92ee274daa2f0d92a564a7cb44`. Branch:
`phase-l/l7-a0-ci-release-inventory-contract`.

Evidence: [L7-A0 run](acceptance_runs/l7-a0-20261023T164344Z/manifest.json).
The containing Git commit/tree identifies the final governance candidate; the PR
records those exact identities without a circular self-referential commit field.
`source_inventory.json` binds reviewed entry files; manifest hashes bind evidence
bytes. This report and the five front doors are also bound by the containing tree.

L6 remains **CLOSED** under `PHASE_L_L6_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.
L7 is **STARTED**. A1+ implementation, stable release/publication, merge/auto-merge,
and Phase M are **NOT AUTHORIZED**. Phase L is **NOT CLOSED**.
This disposition does not certify green CI or approve a stable release.

## Current evidence and authority

Roadmap V3.2 historical **L.8 CI / Release Governance** maps to current **L7**.
Historical L.7 extension architecture maps to current L5. The frozen L0-D02 target
is provisionally v1.5.0. Historical L0-D03 records Windows 10 and Windows 11 x64,
but the accepted [prospective supersession](PHASE_L_L6_WINDOWS11_TIER1_PROSPECTIVE_POLICY_SUPERSESSION_2026-10-21.md)
under `USER_CHAT_2026-10-21_WINDOWS11_NATIVE_TIER1_BASELINE_SUPERSESSION`
sets current L6/L7 release-blocking Native Tier-1 to **Windows 11 x64 only**.
Windows 10 is not release-blocking; historical L0-D03 remains unchanged.
The machine-readable obligation matrix covers all 15 required obligations. None
is declared satisfied merely because a YAML file exists.

Five workflow files exist in the exact entry tree. All use Python 3.11 and install
`requirements.txt`; browser E2E additionally installs browser requirements and
the exact lock. Default CI, full non-network, Windows compatibility and browser
E2E are manual. Release Validation also triggers on `release: published`, which
is too late to act as a pre-publication gate. There are no current PR triggers or
release artifact outputs. Checkout/setup/pip/browser installation use network;
non-network test markers are not evidence of an OS-enforced egress boundary.
Action major tags, latest runner images and range resolution leave mutable inputs.

Read-only GitHub GETs show main unprotected, no rulesets or effective main rules,
no required PR/reviews/status checks, no branch-rule force-push/deletion/signed
commit/linear-history protection. Merge, squash and rebase methods are enabled;
auto-merge is disabled. Actions are enabled with all actions allowed and no SHA
pinning requirement. The protection endpoint explicitly returns “Branch not
protected”, corroborated by successful branch/rule endpoints. No permissions gap
was used to infer PASS. No settings were changed.

GitHub Actions retains an active registry entry for historical
`phase-h-h-act-h1-rollback-check.yml`, absent from the exact current tree. It is
recorded separately from the five current workflows. Recent hosted runs refer to
older commits; their success does not establish green CI for this entry.

All 23 configured profiles and five deprecated aliases are inventoried with exact
definitions. Proposed release-blocking composition centers on current deterministic
default/full non-network and necessary security/architecture/J regression coverage;
A1 must select a nonredundant, green set. Inner-loop/component diagnostics remain
nonblocking unless promoted. Operator/browser/release preflight is manual
acceptance; bounded-live is a separately authorized one-shot; historical replay is
diagnostic. These are governance roles, not changes to runner behavior or markers.
Runtime estimates were not measured in A0. Configured timeouts are not durations.

## CI debt and release checklist conflict

Accepted A6 evidence remains **1245 passed / 45 failed / 4 skipped / 5 deselected**,
1299 collected, overall **FAIL**, candidate-only failures **0**. Exact failed node
sets match between accepted base and candidate. Full Git diff from accepted A6
head to this entry contains only six governance/front-door files; product, tests,
profiles, dependencies and workflows are unchanged. This justifies bounded reuse
of that evidence, not a claim that A0 reran CI or that hosted CI is green.

| Provisional classification | Count | A1 obligation |
| --- | ---: | --- |
| ENVIRONMENT_DEPENDENT | 1 | Node-launch prerequisite in bounded PATH |
| TEST_INFRASTRUCTURE_DEFECT | 2 | Launcher tests lack explicit initialized installation; preserve preload-before-bind checks |
| HISTORICAL_GOVERNANCE_ASSERTION | 12 | Old call-shape/catalog projection or literal Phase-J-not-started state |
| DECISION_REQUIRED | 30 | 28 missing Security Master snapshot cases, one localhost readiness case, one MCP dispatch error |

Every node, message, source XML reference, failure-text hash and rationale is
retained. Classification is provisional, not a product-defect exemption. Missing
isolated Security Master fixtures/root binding is a hypothesis requiring A1 proof.
The localhost/MCP failures are not explained away by that hypothesis.

Expanded validation remains **525 passed / 2 failed, overall FAIL**. Its two L5
frozen-scope assertions report later accepted L6 network/backup/mode files as
`A5_NEW_FAMILY_DETECTED`. They provisionally remain historical governance assertions.
They may become nonblocking historical diagnostics only after accepted A1
adjudication and equivalent current coverage. They are not deleted or modified.
This expanded subset is **not** a FULL_NON_NETWORK result.

The release checklist promises DEFAULT_CI and FULL_NON_NETWORK PASS. Default CI
contradicts that promise; current complete FULL_NON_NETWORK PASS is unproven.
The checklist also mentions a Windows label trigger absent from YAML. A1 owns
green-profile/checklist reconciliation; A2 owns actual release integration and
trigger alignment. The historical checklist remains unchanged in A0.

**Frozen policy:** all future release-blocking deterministic checks must PASS.
Green CI is conditionally achievable through valid defect/setup repairs and
explicit historical adjudication, preserving immutable evidence and equivalent
current safeguards. There is no authority to hide unresolved failures, broadly
exclude files, relabel current product defects as history, or weaken assertions.
Historical suites may remain red only under specifically accepted classification
and exclusion from blocking status. A0 implements no such exclusion.

## Runtime, dependencies, compatibility and version

| Surface | Current evidence | Required later decision |
| --- | --- | --- |
| GitHub CI | Python 3.11 | A3 align required release runtime; A4 compatibility review |
| Developer verification/onboarding | Explicit support for 3.11 or 3.13 | No silent removal of 3.11; 3.12 not currently declared supported |
| Native C | CPython 3.13 x64, Windows 11, 49 exact wheel hashes | A2 release integration; A3 dependency/runtime authority |
| Fresh Sandbox | Windows 11 x64, official CPython 3.13.9 | Accepted L6 evidence, not new release acceptance |
| Docker | Linux/amd64 Alpine, Python 3.13.17, 48 exact wheel hashes | A2/A3 release build/runtime evidence |
| Lock generation | CPython 3.11.15 Windows x86_64, pip 26.2.1 | Reconcile generation environment and consumer locks |

Python 3.13 as canonical release/required CI is a candidate policy, not an adopted
support change. A3 owns runtime/dependency policy with A4 compatibility review.
A2 implements and validates the already-decided Windows 11 x64 Native policy.
It does not re-decide whether Windows 10 is release-blocking. Python version
policy remains a separate later decision; this correction preserves L7-EXIT-05.

`requirements.txt` has ranges except the exact MCP pin; `requirements-lock.txt`
has exact transitive versions/platform markers but no hashes. Native and Docker
derive platform-specific, hash-pinned artifacts. Browser requirements include the
exact lock plus Playwright 1.55.0, while browser binaries/OS prerequisites need
their own provenance. A3 must freeze named dependency authorities for developer
compatibility, required CI, Native, Docker and browser acceptance. No versions,
dependency files or support behavior change here.

MCP remains **CURRENT_EXACT_PIN: mcp==1.29.0** and
**COMPATIBILITY_RANGE_NOT_YET_DECIDED**, owned by A4. Accepted launcher/schema,
tool registration, error serialization, stdio/session behavior and package closure
depend on verified SDK behavior. Existing official wheel hashes and exact-pin
tests do not prove a multi-version range. Exact pins risk delayed fixes; ranges
risk unreviewed parser/schema/transport and transitive changes. The inventoried
MCP tests and exact-six authority must survive either decision.

`VERSION` remains **1.0.0**. Provisional target is **1.5.0**; final choice belongs
to A4. No known intentional v2 trigger was found in accepted L1–L6 compatibility
evidence. A4 must still establish Request/Result/Audit/MCP and state compatibility,
including unresolved tests, before deciding. There is no v1.5.0 approval in A0.

## Artifact integrity and release governance

Historical published v1.0.0 MCPB/checksum/manifest and v1.0.0-rc.1 prerelease
manifest remain separate from local RC documentation and L6 portability evidence.
Observed tag/release lists contain no v1.5.0 or v2.0.0 release. No assets were
downloaded, built, uploaded or published in A0.

L6 Native `TW-Market-1.0.0-windows-x64.zip` remains bound to SHA-256
`6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04`.
Docker source/replacement identities remain
`sha256:2b25c1e54879b0761d3c0a3591236cb2a1f820c1530fee25f643ec93cf962675` and
`sha256:98bafa33505e0d5f4c088e58949e388768b21b0a0741f4da5649eff539f91323`.
They are **L6 acceptance artifacts**, not future stable release outputs. The
replacement image's post-reboot local unavailability remains a retained limitation;
persisted accepted evidence is not a promise of current local availability.

The V1 release schema types commit/tree, version and arbitrary artifact hashes.
Its current builder hashes VERSION, requirements-lock and public contracts.
Native/Docker manifests add platform/member/dependency facts but do not form one
typed final release contract linking runtime, compatibility, CI/live evidence,
signatures and publication location. A6 owns manifest integration; A3/A4/A5 supply
dependency/provenance, compatibility and live evidence. No schema is replaced here.

Native fixed member order/timestamps, exact Git blobs and wheel hashes support
repeatable inputs/member integrity; cross-host ZIP byte equality remains unproven.
Docker exact base digest, source and hashes support repeatable inputs; different
source/replacement image identities prove neither image digest reproducibility nor
failure of state portability. A3 must specify acceptable reproducibility versus
provenance and toolchain controls. Mutable hosted CI inputs need reconciliation.

GitHub verifies the entry merge commit, not every future candidate. Historical
checksums exist. Tag signatures, Windows signing and publisher policy are not
established by metadata. Inspected contracts have no manifest-signature or SLSA
generation/publication step; dependency manifests are not a complete first-party
release SBOM. Integrity, signing, publisher identity and supply-chain provenance
are distinct decisions. A3/A6 own the policy; no signing/secrets setup is authorized.

The generic gate matrix remains `local_only_fixture_only`, controlled live and
production refresh false. Historical phase-specific consumed live authority is
not renewed. Future A5 acceptance requires exact Owner authority, source/target
allowlists, request/time budgets, bounded retry policy, isolated nonproduction
state and request/response/provenance retention. Transport-degraded outcomes must
remain distinguishable from deterministic contract drift; neither silently grants
release acceptance. Production refresh remains outside L7 publication authority.

## Frozen sequence and final exit contract

1. **A1:** define/prove green deterministic required CI; adjudicate historical debt.
2. **A2:** integrate fresh clone, Windows, Native and Docker release validation.
3. **A3:** freeze dependency/runtime, reproducibility and supply-chain policy.
4. **A4:** decide public/state compatibility, SDK pin/range and final version.
5. **A5:** execute separately authorized bounded-live release acceptance.
6. **A6:** freeze RC source/artifacts, complete manifest/notes and publication preflight.
7. **A7:** separately authorized publication, post-release verification and technical exit.

A2 can integrate against current accepted inputs, but A3/A4 decisions must feed
repeat release validation before A6. A7 technical exit does not auto-close Phase L;
Owner final acceptance remains required.

Branch sequence is **define trustworthy checks → prove green/stable → authorize
PR triggers → observe actual hosted stability → authorize required status checks
→ authorize appropriate branch/ruleset protection**. A6 owns settings decisions;
specific changes to PR/reviews/bypass/force-push/deletion/signing/linear-history or
merge policies need later authorization. No currently-red gate is made required.

`candidate_l7_exit_criteria.json` is the canonical **29-item** list for A1–A7,
including deterministic green CI, fresh release validation, exact-six/public/state
compatibility, dependency/runtime/version decisions, complete manifest and artifact
provenance, bounded live, explicit publication, post-release proof and final Phase L
obligations. Every criterion is NOT_YET_ACCEPTED_FOR_L7_RELEASE.

The gap register contains **21 owned gaps**; the erroneous Windows platform decision gap is removed;
none is unowned. Release blockers are future work, not an A0 claim of readiness.
The A0 inventory resolves the governance ambiguity by naming evidence, decisions,
ownership and required proof; implementation awaits separate authorization.

## Validation and mutation boundary

`required_validators.json`, `historical_evidence_integrity.json`,
`scope_diff_verification.json`, `final_inventory_review.json` and manifest
verification record actual deterministic checks. Review-only harness compilation
and exact changed-path checks are required before commit/push/PR. No large CI or
L6 P1–P6 replay is performed.

Product/runtime, test semantics, workflows, dependencies, VERSION and GitHub
settings remain unchanged. Release/publication actions, live-provider requests,
production-state mutations and D-drive access commands are **0**. These are
task-action counts plus diff containment, not system-wide telemetry claims.
After updating the PR, stop for independent re-review and Owner acceptance.

The review of candidate `3893c9c7f21b33378b8d8a27c4170846a5c7e4cc` returned
`L7_A0_INDEPENDENT_REVIEW_CHANGES_REQUIRED`: it incorrectly reopened the accepted
Native platform policy as L7-GAP-22. The bounded correction removes that gap,
reconciles the accepted prospective authority and updates counts consistently.
The 29-item exit contract, including L7-EXIT-05, is byte-unchanged. This repair
does not claim independent acceptance; re-review remains pending. See
`review_correction.json` in the A0 evidence run.
