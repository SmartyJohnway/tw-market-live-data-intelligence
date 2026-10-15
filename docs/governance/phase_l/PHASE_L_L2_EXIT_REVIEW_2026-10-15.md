# Phase L L2 — Replay / Retention / Migration Exit Review

**Review date:** 2026-10-15
**Review base:** `origin/main@a23119a7243627b140c5678911e6e522b94ddda2`
**Technical disposition:** `PHASE_L_L2_EXIT_REVIEW_PASS`
**L2 technical exit:** PASS
**Owner final closure:** `PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`
**L2 status:** **CLOSED**
**Merged:** PR #353 / `b84ba8a4ac4819d115de33e55cf9adf2a5801e00`
**L3-L7:** NOT AUTHORIZED

## 1. Authority and review scope

This exit review follows the current recovery index, `PROJECT.md`, `HANDOFF.md`,
the current Phase L section of `ROADMAP.md`, frozen L0, and the accepted L2-A0
through A6/A6-R1 authorities. Current Git `origin/main` and its merged
governance records were checked before review. PR #342 introduced L2 entry,
A0, and A1; PRs #343/#344, #345/#346, #347/#348, #349/#350, and #351/#352
carry the A2, A3, A4, A5, and A6 implementation/closure chain respectively.
No Phase G-K history was needed to decide an L2 obligation.

The review is an integrated technical exit assessment. It adds no product
runtime behavior and makes no Owner final-closure decision. A0-A6 are present
on the reviewed main: A0/A1 entry PR #342
(`2398e1fa4c3501ccd9e65efdfa428beaad05117d`), A2 PR #343
(`bdd9588bc34ab25af8e22ba7cd7900160a56abf5`),
A3 PR #345 (`378acb454a4e1e4e82e2be14b5957dc7d912f751`), A4 PR #347
(`fb2fef0c50c3ee50581bc62af534b36116b332e7`), A5 PR #349
(`97386f756f2dcc6dbf4d3ee7934a41066fa1b0c2`), and A6 PR #351
(`e090ae353cb00d3b1d076cdb40c5a76cf2229d5d`). A6 merge-closure PR #352 is
the reviewed HEAD `a23119a7243627b140c5678911e6e522b94ddda2`. The recovery
index and merged A6 record confirm A0 complete, A1/A1-R1 frozen, and A2-A6
Owner-accepted/closed. A6-R1 is included in the A6 accepted boundary.

## 2. L2 obligation matrix

| Obligation | Required semantic | Current authority | Exit finding |
|---|---|---|---|
| Read existing | No hidden write or refetch | A1 / A2 | PASS |
| Evidence replay | Retained evidence only; historical timestamps remain authoritative | A1 / A2 | PASS |
| Refetch | A separate new governed execution with explicit authorization | A1 | PASS |
| Missing retained evidence | Typed fail-closed result; never fetch replacement evidence | A1 / A2 | PASS |
| Retention classification | Explicit canonical, governed, derived, ephemeral, and unknown classes | A3 | PASS |
| Unknown retention | `UNCLASSIFIED_REQUIRES_POLICY`; no automatic deletion | A3 | PASS |
| Backup | Explicit caller-declared member set and bounded package | A4 | PASS |
| Backup integrity | Versioned manifest, member SHA-256, manifest integrity, contained paths | A4 | PASS |
| Restore compatibility | Explicit target contract and independently derived version outcome | A5 | PASS |
| Direct restore | Isolated destination; exact declared bytes; no activation | A5 | PASS |
| Older migratable state | A5 emits `MIGRATION_REQUIRED`; A6 independently binds A4/A5 lineage | A5 / A6-R1 | PASS |
| Newer unsupported state | `UNSUPPORTED_NEWER_STATE`; fail closed | A5 / A6 | PASS |
| Migration preview | Explicit, deterministic, read-only plan bound to source/contract/registry | A6 | PASS |
| Checkpoint | Verified immutable `SOURCE_A4_BACKUP`; incomplete scope fails closed | A6-R1 | PASS |
| Migration apply | Explicit copy-on-write lifecycle; only registered implemented transformers run | A6 | PASS |
| Rollback | Retained A4 bytes to a new isolated candidate; no guessed inverse transform | A6 / A6-R1 | PASS |
| Activation | Not part of L2; restored/migrated candidates are not active installations | L0 / A5 / A6 | DEFER |
| Physical state roots | Explicit caller roots remain bounded; final mapping belongs to L6 | L0 / A4-A6 | DEFER |
| Packaging | Native/Docker packaging and P1-P6 portability belong to L6 | L0 / Roadmap | DEFER |

No deferred row is a frozen L2 requirement or an exit blocker.

## 3. Replay and refetch finding

The frozen distinction remains intact:

```text
READ_EXISTING
!= REPLAY_FROM_RETAINED_EVIDENCE
!= REFETCH_CURRENT_SOURCE
```

Read and replay are local, non-authorizing operations. A2 requires retained F3
and other required lineage; missing retained evidence is a typed unavailable
state and is not reconstructed from current Security Master or source data.
Refetch remains a separate new execution through validation, preview, explicit
authorization, and execute-once. No A2/A5/A6 behavior crosses these boundaries.

## 4. Retention finding

A3 gives deterministic bounded classifications and fails unknown/unbound input
to `UNCLASSIFIED_REQUIRES_POLICY`. Canonical user state is not disposable just
because it can be downloaded again. Governed evidence is protected; an
ephemeral classification requires positive ownership/binding and proof of no
governed reference. `POTENTIALLY_ELIGIBLE` is not deletion authorization, and
the classifier performs no deletion or cleanup.

Numeric retention durations and retained rollback-release counts remain
deliberately unset because L0 classified them as evidence-dependent deferred
implementation values rather than frozen L2 architecture requirements.

Until later explicit authority exists, canonical user state, governed evidence,
and unclassified state are not subject to automatic deletion merely because no
duration has been assigned. The retention obligation passes with operational
values deferred.

## 5. Backup, restore, compatibility, and migration findings

A4 copies only explicit caller-declared members, applies A3 policy, enforces
caller bounds and Windows Tier-1 path containment, and verifies member and
manifest SHA-256 without source mutation or network. Its
`EXPLICIT_DECLARED_MEMBERS_ONLY` scope is not whole-installation completeness.

A5 reuses A4 verification. `BACKUP_VERIFIED` proves package integrity only;
compatibility is separately derived. `DIRECT_RESTORE_COMPATIBLE` writes exact
bytes to an isolated target. `MIGRATION_REQUIRED`, unknown compatibility, and
unsupported newer state do not create a restore target. Restore does not
migrate or activate state.

A6-R1 correctly defines migration source authority as verified A4 backup plus
manifest-bound A5 `CompatibilityAttestation` and an independently derived A5
`MIGRATION_REQUIRED` result. It does not require an impossible A5 restore
receipt and does not change A5 semantics. Migration follows inspect, preview,
verified A4 checkpoint, copy-on-write apply, verification, and rollback from
retained A4 bytes. Source/checkpoint and active installation remain unchanged.

The only current production migration ID,
`watchlist-schema-v0-to-v1`, is `KNOWN_NOT_IMPLEMENTED` because authoritative
v0 schema/fixture/transform authority is absent. This is correct fail-closed
lifecycle behavior, not an L2 blocker. No production transformer is available;
the test-only synthetic transformer proves generic machinery only.

## 6. No-silent-migration, rollback, and activation

The accepted contracts require migration to be explicit, previewed,
checkpointed, bounded, and independently verified. A5 restore, reads, startup,
and status do not implicitly migrate or repair state. Unsupported newer state
cannot be relabeled as a migration path. Rollback uses retained pre-migration
A4 bytes rather than an inverse SQL/schema guess. A restored, migrated, or
rollback candidate is never an active installation or activation authority.

## 7. Integrated deterministic gate

Command:

```text
python -m pytest -q tests/unit/test_unified_replay_inspector.py tests/unit/test_unified_retention_inventory.py tests/unit/test_unified_backup.py tests/unit/test_unified_restore.py tests/unit/test_unified_migration.py tests/unit/test_m8r_08b_mcp_tool_contracts.py tests/unit/test_m8r_09_persistent_watchlists.py
```

Result: **129 passed, 393 warnings, 0 failed**. All warnings are the existing
Persistent Watchlist `jsonschema.RefResolver` deprecation at
`scripts/m8r_09_persistent_watchlists.py:90`; the test run showed no failure or
behavioral change associated with it. Full/default CI and live acceptance were
not run; neither is an L2 exit hard gate under current authority.

The selected accepted tests cover the required cross-layer checks:

| Check | Evidence in selected tests | Result |
|---|---|---|
| R1 missing evidence does not acquire source data | A2 read-only/network sentinels and missing-artifact cases | PASS |
| R2 retention classification does not delete | A3 pure classifier and filesystem/SQLite/network sentinels | PASS |
| R3 backup verification does not authorize restore | A4 package verification is separate from A5 compatibility/restore calls | PASS |
| R4 `MIGRATION_REQUIRED` creates no A5 target | `test_migration_required_is_inspect_only_and_creates_no_target` | PASS |
| R5 production unimplemented migration writes no staging target | `test_production_known_not_implemented_dispatch_writes_nothing` | PASS |
| R6 rollback does not mutate A4 checkpoint | A6 test-only lifecycle compares source/checkpoint inventory and hashes | PASS |
| R7 exact-six MCP remains unchanged | `test_exactly_six_tool_contracts_with_one_bounded_action` | PASS |

The no-network finding is bounded to the selected deterministic suite and its
socket/acquisition sentinels: zero market/source acquisition and zero external
network calls were observed. All backup, restore, migration, and Watchlist
fixtures use isolated temporary roots; tests performed zero production-state
mutation. The A4 package and source bytes are checked for immutability in their
respective accepted tests.

## 8. Public and evidence-family boundary

The exact six MCP names remain:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

The contract test asserts exactly six. This exit review changes no runtime
files, HTTP API, schema, Catalog/Route/Executor, authorization semantics, or
evidence family. `financial_statements` remains outside the current capability
scope. L2 adds no trading, broker, or investment-advice semantics.

## 9. Deferred items and limitations

The following remain later Phase L boundaries, not L2 blockers: physical
Windows state/config/log paths; final `init` and installation UX; whole
installation automatic state discovery; Native Windows installer and Docker
packaging; P1-P6 portability acceptance; source drift probes; security/load/
concurrency ceilings and large supported-result acceptance; evidence-family
extension contract; MCP SDK compatibility range; final v1.5/v2 decision; L7
release CI profiles; numeric retention durations and retained rollback release
counts; and Linux/macOS Tier-1 promotion.

The current backup/restore/migration APIs intentionally use explicit trusted
caller-declared members and roots. They do not claim automatic discovery or
whole-installation completeness. No production historical migration can run
until an authoritative old-state transformation is supplied by a future
authorized boundary.

## 10. Independent exact-head review

Independent reviewer verification of PR #353 re-ran the same integrated deterministic gate and confirmed **129 passed, 393 existing warnings, 0 failed**. The reviewer also verified that the accepted A0-A6 and A6 merge-closure commits are ancestors of the reviewed `origin/main`, and that the PR changes governance/front-door files only.

One governance-consistency defect was found outside the primary current handoff summary: the later `HANDOFF.md` section titled `Explicit stop boundary` still described L2 only through A2. Because that section presents itself as a current stop boundary rather than historical evidence, it was reconciled to the same A7 technical-exit / Owner-closure-pending state. No runtime, test, schema, MCP, evidence-family, market/source, or product-state behavior changed. `git diff --check` remained clean.

## 11. Exit decision and next boundary

No unresolved L2 blocker was found against frozen L0 and accepted A0-A6
authority. Technical disposition is:

```text
PHASE_L_L2_EXIT_REVIEW_PASS
L2 technical exit = PASS
Owner final closure = PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS
L2 status = CLOSED
PR #353 merge = b84ba8a4ac4819d115de33e55cf9adf2a5801e00
L3-L7 = NOT AUTHORIZED
```

Owner final closure is recorded under `PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` and PR #353
is merged at `b84ba8a4ac4819d115de33e55cf9adf2a5801e00`. L2 is therefore CLOSED. This closure does not
authorize activation or begin L3; L3-L7 remain outside the accepted boundary and require separate
explicit Owner authorization.
