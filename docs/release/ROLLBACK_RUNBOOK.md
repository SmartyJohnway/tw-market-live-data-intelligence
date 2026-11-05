# Stable Release Rollback and Recovery Boundaries

**Release reference:** [v1.5.1 publication record](V1_5_1_RELEASE_PUBLICATION.md).

## 1. Local operator-runtime incident

1. Stop the affected TW-Market Local Service using the supported Launcher
   or `tw-market.cmd stop --json` command. Do not use destructive Docker
   `down --volumes` as a routine rollback.
2. Retain HOME, STATE_ROOT, Security Master, Watchlists, Control Package,
   result/audit evidence and relevant logs; they are not disposable build files.
3. Verify the package zip against its published SHA-256. If the derived
   Native runtime is suspect, follow the packaged documented rebuild/bootstrap
   procedure without deleting installation state.
4. Diagnose the current installation, then explicitly re-start if authorized;
   `init` or service startup is not Security Master/live-data acquisition.
5. Do not mix storage roots or assume legacy persisted state can be
   automatically downgraded or migrated between release lines.

## 2. Returning to an older published version

The separately frozen [v1.5.0 GitHub Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0)
is still available. A **new isolated installation**, backup/restore planning,
data format compatibility and explicit operator decision are required before
using an older application package against current durable state. This
runbook does **not** assert that automatic rollback of state is supported.

## 3. Released-source or asset defect

Do **not** move/retarget the annotated `v1.5.1` Tag, rewrite its six assets,
modify its Publication Manifest, or silently substitute a build.
Handle product defects with a new separately authorized corrective version
and its own verification/publication gate. No direct Registry/Docker
publication is implied.

## 4. Non-goals

Documentation-only commits on `main` do not update old release binaries.
No startup market fetch, scheduler, broker function, automatic Watchlist
refresh, Phase M work, or execution retry is authorized by rollback.
