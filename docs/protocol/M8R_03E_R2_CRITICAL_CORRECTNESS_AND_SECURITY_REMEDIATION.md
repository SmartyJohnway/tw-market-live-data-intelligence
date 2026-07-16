# M8R-03E-R2 critical correctness and security remediation

Baseline SHA: `1c2144498b524e52b2bf21fce8ed00683d9eb3a7`.

Disposition: **GO_WITH_CAVEATS_PENDING_WINDOWS_WORKFLOW_CONFIRMATION**.

R2 introduces `scripts/m8r_filesystem_safety.py` as the centralized containment primitive and routes the M8R-03E context handoff output surface and M8R-03D controlled-execution artifact surface through it. The primitive rejects lexical traversal, absolute replacement, Windows drive/UNC candidate inputs, prefix collision, symlink-parent escape, and destination symlink writes. Atomic writes use temporary files created inside the validated authorized root.

Authorization composition is tested at the nearest controlled-execution boundary: `scripts/m8r_03d_watchlist_controlled_executor.py`. The M8R-03E handoff writer consumes already-authorized upstream artifacts, so it does not directly validate M8R-03D authorization tokens. The R2 tests prove missing authorization, wrong-scope authorization, valid authorization with escaping output path, invalid authorization with escaping output path, valid authorization with valid output path, and replay/output-root independence.

Caveats: portable TOCTOU guarantees are best-effort; Windows junction/reparse behavior requires platform smoke/follow-up and is not claimed as fully race-proof.
