# Post-Phase-J Portability & Runtime Hygiene

Status: CURRENT maintenance guidance after Phase J closure.

## Purpose

Keep acceptance infrastructure separate from product runtime, prevent installation-local data from entering Git, and bound local disk growth without weakening evidence or rollback semantics.

## Retention classes

| Class | Examples | Default disposition |
|---|---|---|
| Canonical tracked authority | contracts, schemas, governance ledgers, accepted hashes | KEEP in Git |
| Active installation state | `data/security_master/active.json`, active release, watchlists | KEEP locally |
| Rollback-capable qualified releases | prior immutable qualified Security Master releases | KEEP until explicit retention/rollback policy selects what may retire/prune |
| Post-qualification candidate copy | `data/security_master/candidates/<active-release-id>` | CLEANABLE after release hash equivalence is verified |
| Reproducible acquisition/build inputs | old Security Master input bundles and compact indexes | ARCHIVE/PRUNE candidate; never required for normal active-release load unless a legacy compatibility path still references them |
| Acceptance runtime evidence | retained package and small Attempt receipts/logs | KEEP while uniquely useful; prefer hashes/compact receipts over duplicated runtime trees |
| Third-party acceptance distribution | pinned Codex/host bundles | DELETE after closure when source/install path remains obtainable and committed inventory/hashes exist |
| Ephemeral test/cache state | pytest temp, caches, scratch roots | DELETE |

## Phase J closure cleanup

The Git-external Phase-J pinned Codex distribution was an acceptance-only dependency, not a TW-Market product runtime dependency. After PR #326 merged, the 741.45 MiB `codex-pinned` tree was removed. The retained J1-21 package and small Attempt 4–6 evidence were preserved.

## Installation-local `data/` boundary

No path under `data/` is tracked by Git. A clean clone is therefore allowed to have no `data/` directory and to enter the governed `SECURITY_MASTER_NOT_INITIALIZED` state. The repository should ignore `data/` as a whole rather than enumerate selected runtime subdirectories.

This prevents local Security Master candidates, releases, watchlists, and acceptance-run control packages from appearing as accidental Git additions. Canonical acceptance evidence belongs under tracked `docs/` locations, not under installation-local `data/`.

## Security Master retention

Current runtime loading uses `active.json` plus `releases/<active-release-id>`. A qualified candidate directory is not consulted after qualification/activation. The active release must never be deleted.

Prior qualified releases are not disposable cache: the release contract permits rollback by selecting another immutable qualified release. Do not bulk-delete prior releases until a separate retention policy defines how many trusted rollback releases to retain and how retirement/pruning preserves provenance.

Legacy `runtime_identity_indexes` and their committed compatibility pointers require separate adjudication before deletion. Old input bundles are build/reproducibility material rather than normal runtime inputs, but should be pruned only after their historical provenance obligations are explicitly classified.

## Portability rule

Current product/runtime code should derive repository and installation paths from the checkout/configuration or environment, not from a developer-specific drive, username, Codex installation, or Phase-J runtime directory. Historical governance evidence may retain the exact absolute paths observed during its original run.

## Cleanup performed on 2026-10-12

Two Git-external/local cleanup actions were completed after Phase J merged:

1. Removed the Phase-J `codex-pinned` acceptance distribution: **741.45 MiB** reclaimed.
2. Removed the post-qualification candidate copy for active release `security-master-20260926T151841Z`: **86.05 MiB** reclaimed.

Before candidate removal, its `index.json` SHA-256 exactly matched the active qualified release index (`665d69e53588fa6cd723e434902946a43ac4f712920b0c4ec2adf91b556f4c10`) and its qualification hash also matched. `load_active_identity_service()` resolved `TWSE:2330` successfully both before and after deletion.

Total directly reclaimed in this pass: approximately **827.5 MiB**. No qualified rollback release, active pointer/release, watchlist, retained Phase-J package, or Attempt 4–6 evidence was deleted.

## Portable Skill synchronization finding

The first clean-room clone exposed a pre-existing sync defect already present on merged `main`: the canonical V3 capability catalog SHA-256 was `00e6dad9fff81be1151e2ba1001396b0ef01f1fa2d48a7f17fadf235ba7fb2c5`, while the checked-in portable Skill projection still recorded `35134ae437fccdaa2a95e261b2a7f81210c7175fbf9f1c05e251907c7f11ddf1`.

Regeneration with the existing `scripts/generate_portable_catalog.py` corrected only generated portable artifacts. The meaningful product truth synchronized into the portable projection is the already-canonical `corporate_action_context` state: TWSE selected-route runtime executable, no TPEx H2 activation, with the existing bounded coverage/provider caveats. No new capability or route was introduced by this maintenance work.

## Additional local-state cleanup

After confirming the default production loader uses the installation-local active release and does not fall back to the legacy compact pointer, two superseded local build/runtime classes were removed:

- old Security Master input bundles: **414.14 MiB**;
- legacy compact `runtime_identity_indexes`: **70.10 MiB**.

The active release source snapshot (`dryrun-m8r06-01b-20260926T151849Z`) was not one of the removed old input bundles. Future explicit live updates recreate their own input bundle directory. The legacy compact pointer remains a migration/test adapter in source control but is not the default production authority.

After cleanup, the installation-local `data/` tree is approximately **563.41 MiB (0.55 GiB)** and still contains all six qualified releases, including the active release. Default production identity loading and `TWSE:2330` resolution were verified after deletion.

Combined direct reclamation from the pre-cleanup machine state is approximately **1,311.7 MiB (1.28 GiB)**: 741.45 MiB Phase-J Codex distribution + 86.05 MiB duplicate candidate + 484.24 MiB old input/legacy-index material.

## Clean-room portability proof

A `git clone --no-local` of the maintenance branch was created in a fresh directory with no inherited `data/` tree. The clone reported no tracked data files and entered the expected fresh-install boundary.

Validation in that clean clone:

- fresh-install / portability focused tests: **8 passed**;
- portable capability catalog deep-sync validator: **PASS**;
- runtime Skill/guide six-tool sync validator: **PASS**;
- `python -m compileall -q scripts server tests`: **PASS**;
- Git worktree after validation: clean;
- dependency manifests contained no developer-specific `file:`/`C:\`/`D:\`/home path references.

This proves the repository can be cloned and validated without the original machine's Phase-J runtime bundle or installation-local `data/`. It does not imply that a fresh user already has an initialized Security Master; `NOT_INITIALIZED` remains the intended fresh-install state until the user explicitly builds/activates local identity authority.
