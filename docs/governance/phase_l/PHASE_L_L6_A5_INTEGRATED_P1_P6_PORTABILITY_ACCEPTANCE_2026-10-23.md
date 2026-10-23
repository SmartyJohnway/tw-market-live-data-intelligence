# Phase L / L6-A5 — Integrated P1–P6 Portability Acceptance

Technical disposition: `L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_PASS`.
Independent review: `L6_A5_INDEPENDENT_TECHNICAL_REVIEW_PASS`.
Owner disposition: `L6_A5_OWNER_ACCEPTED_FOR_MERGE`.
PR #404 normal-merged exact accepted candidate `32bc480cccdd7eb394062ccfe34a44958fc56bf1` at
`08bec63ec3d924d2c3b206ecc4fcc017b259ea75`, merged tree `041f7c660a3fba40b84d5fbab869c2ee353919ac`. Merge parents are
`d5dac702c25e9728db86e9ef32f4fe8185086b89` and the accepted A5 candidate; GitHub merge verification is valid.
This is not Phase L/L6 closure.

Authority: `USER_CHAT_2026-10-23_PHASE_L_L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_AUTHORIZATION`,
including supplemental Windows Sandbox enablement/environment authority and the
instruction to continue after reboot. L6-A6, L7, Phase M, installer/release work
and image publication remain NOT AUTHORIZED.

## Candidate binding

Exact authorized entry: `d5dac702c25e9728db86e9ef32f4fe8185086b89`,
tree `43aa778bbdc8a2bff016520d0cd1aff04a83b953`. Re-fetched main after reboot;
it remains the exact entry. No rebase or base substitution occurred.

All final product/runtime acceptance uses committed source
`3707c553497240f6ff0f7e5358301395fd60205a`, tree
`946e765b26b2520f623672dc49a51c913139f44f`. The accepted final governance candidate is
`32bc480cccdd7eb394062ccfe34a44958fc56bf1`, tree `041f7c660a3fba40b84d5fbab869c2ee353919ac`; PR #404 normal-merged that exact candidate at
`08bec63ec3d924d2c3b206ecc4fcc017b259ea75`. Do not confuse the acceptance-source identity with the accepted
candidate or merge commit.

Native ZIP SHA-256:
`6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04`.
338 ZIP members, 337 manifest entries, 49 unchanged hash-pinned Windows wheels.
Native and Docker share 277 exact source Git blobs. Docker uses the unchanged
48-wheel lock and pinned Alpine base
`python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741`.
Source image `sha256:2b25c1e54879b0761d3c0a3591236cb2a1f820c1530fee25f643ec93cf962675`;
replacement image `sha256:98bafa33505e0d5f4c088e58949e388768b21b0a0741f4da5649eff539f91323`.
The replacement's completed runtime evidence persists; its local image reference
was unavailable after the unexpected reboot. No registry publication occurred.

## Implementation

The two builders accept an opt-in exact A5 entry, preserving prior A3/A4
defaults. A thin explicit-member A1 adapter calls the existing canonical L2
backup/verify/isolated-restore authorities. It never discovers state or activates
a restore. Only explicitly bound v1 loopback endpoint settings are admitted;
paths, installation identity, runtime/PID/cache/log/temp and arbitrary fields
are excluded. Settings admission reuses A1's bounded 2 MiB JSON reader and
duplicate-key/reparse checks. Existing unbound-settings omission remains intact.
No new Catalog, Route, Executor, migration engine, public endpoint or MCP tool.

## Actual acceptance

| Profile | Disposition | Actual observation |
| --- | --- | --- |
| P1 | PASS | Package A physically moved away; fresh Package B at deeper spaces/non-ASCII location, same external HOME/STATE and identity, fresh offline venv, idempotent bootstrap and lifecycle/exact-six MCP. |
| P2 | PASS | Actual Sandbox WDAGUtilityAccount SID/profile distinct from host, no inherited owner HOME/state/runtime/PID authority. Separate P2 record retained. |
| P3 | PASS | New disposable Windows 11 Enterprise 26100 x64 guest, no Python/Git/TW state initially; official guest-only CPython prerequisite, offline bootstrap, read-only pre-init, explicit init/idempotence, lifecycle/MCP before and after deterministic explicit Security Master activation. |
| P4 | PASS | Existing L2 CORE and FULL_GOVERNED backup, integrity verification, isolated restore, fresh independent destination identity; qualified Security Master, persistent watchlist and sanitized governed Result/Audit fixtures. |
| P5 | PASS | Actual accepted A3 package/state → current package → old package rollback; identity/settings/durable hashes unchanged; supported schema1, no migration required or executed. |
| P6 | PASS | Fresh Docker volumes, explicit init, no-cache image replacement, identity/state survives; default runtime independently checked; host-loopback publication, peer denial and nonloopback rejection. |

P4 explicit use employs the existing A1/A2 root override seams against the
verified isolated restore; `NONCANONICAL_ROOT_OVERRIDE` remains visible.
Destination installation metadata and canonical state-root identity stay intact.
This is explicit supported use, not automatic adoption or a second restore
authority. The CORE Native→Linux cross-profile probe also passes through
canonical L2 verification/isolated restore and existing readers.

Sandbox instance `1c9a5e7a-ddd0-4a27-9298-aec899eb7598` was launched only
after the previous instance stopped and all Sandbox process counts reached zero.
Only bounded read-only input and separate evidence output were mapped;
network/clipboard were disabled. Official CPython 3.13.9 installer SHA-256
`200ddff856bbff949d2cc1be42e8807c07538abd6b6966d5113a094cf628c5c5`
was Authenticode-verified (Python Software Foundation) and guest hash-verified.
No developer interpreter or checkout was mapped. Completed guest records survived
the host reboot; environment availability alone was never treated as acceptance.

Configuration CLI > ENV > persisted settings > defaults, state-root conflict
rejection, and three stale ownership mutations were exercised. Stop rejected
each wrong installation/token/executable while the owned service remained alive;
the restored genuine ownership record allowed canonical stop. This final
supplemental probe was rerun after reboot. Doctor/pre-init checks are read-only;
Native APP_ROOT fingerprints and Docker read-only-rootfs guard pass.
Provider/live acquisition attempts=0, D-drive access commands=0, owner production
state mutations=0. Runtime guards reject owner-state access, D paths, external
network and out-of-bound writes; deterministic offline fixtures add no provider.

## Validation and limitations

61 focused A5/L2 tests pass. Expanded applicability suite: 525 passed, 2 failed;
the two unchanged L5-A5 historical validators assert no protected product change
since `09d6db51cf242316632bffb7ee96eef88014a039` and also fail on the exact
A5 entry after accepted A4. Later A1/L6 authority explicitly supersedes that
tranche's no-change scope. Their failure is preserved, not suppressed or called
PASS; the other 525 applicable checks cover A1–A4/L2/L4/L5/public-contract paths.

Default CI overall remains FAIL on both exact base and candidate:
1245 passed / 45 failed / 4 skipped / 5 deselected, selected1294/collected1299.
Failure-node comparison gives candidate-only regressions=0. The historical
1246/44 count differs because the same bounded PATH omits Node on both runs;
the extra browser authorization failure is identical. No CI exception is claimed.
Required validators, compile/static checks, diff whitespace checks, scope and
evidence integrity are recorded separately in machine-readable evidence.

Earlier c50 runtime evidence is superseded by fresh 3707 builds/runs after the
bounded JSON-reader repair. A bootstrap stdout UTF-8/CP950 harness mismatch was
corrected using binary capture and fresh offline bootstrap/idempotence verification.
Earlier duplicate Sandbox dialogs and UI-observation limitations are harness
issues, not product acceptance failures. Final guest execution completed with
exit0 and separate P2/P3 records. Historical evidence has not been rewritten.

After reboot the first final-CI wrapper launch inherited CP950 in its parent,
while pytest emitted UTF-8; its summary capture failed after test execution.
That incomplete wrapper result is not PASS evidence. The final run explicitly
sets parent `PYTHONUTF8=1`, restoring the original base/source-run startup
encoding; the wrapper, selection, bounded paths and test semantics are unchanged.

## Evidence and stop boundary

Evidence: [final acceptance directory](acceptance_runs/l6-a5-20261023T132500Z/).
The manifest hashes every committed evidence member, with its own digest computed
over canonical JSON excluding only `self_digest`. Large ZIPs, installers, wheels,
venvs, databases and Docker exports are not committed; exact hashes are retained.
Committed text evidence copies use LF and remove line-end spaces/tabs so the
repository whitespace gate passes. `text_normalization.json` retains the
pre-normalization copy hashes; original logs remain in the bounded acceptance
workspace. Test outcomes and recorded assertions are unchanged.

Technical checks completed, independent review passed, and explicit Owner acceptance
was recorded against exact candidate `32bc480cccdd7eb394062ccfe34a44958fc56bf1`. PR #404 was then normal-merged at
`08bec63ec3d924d2c3b206ecc4fcc017b259ea75`. This merge closes A5 only; L6-A6, L7, Phase M, installer/release work
and image publication remain unauthorized pending separate Owner authority.
