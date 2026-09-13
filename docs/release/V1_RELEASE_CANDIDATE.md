# V1.0.0 final promotion candidate

The repository final-promotion ProductVersion is `1.0.0`; its tracked
authority is the repository-root `VERSION` file. The immutable RC provenance is
the published
[`v1.0.0-rc.1` prerelease](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.0.0-rc.1)
on 2026-09-13. Gate O observation passed without product feature expansion. The
latest stable GitHub Release remains `v0.1.0`; final `v1.0.0` has not yet been
published and Phase G has not started.

## What is in the final promotion candidate

- The Unified Workbench at `/workbench/` for local, explicit operator flows.
- Installation-local Persistent Watchlists with preview/commit mutation,
  immutable revisions, and optimistic concurrency.
- Unified Request validation, capability preview, explicit bounded
  execute-once, canonical Result/Audit, and AI-ready handoff.
- A six-tool Unified MCP surface for capability discovery through handoff
  export.

The final promotion candidate is deliberately not a trading, polling, scheduling, background
refresh, or realtime-guarantee product.

## Installation

```bash
python -m venv .venv
# activate the venv for your shell
python -m pip install -r requirements-lock.txt
python scripts/verify_environment.py
python scripts/manage_security_master.py status
```

Fresh installations correctly report `NOT_INITIALIZED`. An operator may later
run `python scripts/manage_security_master.py update --live`; that explicit,
bounded action may acquire governed official data and is never a startup action.

## Operational contract

Start `python scripts/run_unified_workbench.py` and
`python scripts/run_unified_market_evidence_mcp.py` on loopback. The current
Workbench is `/workbench/`; the legacy Mode-A route redirects to it. The MCP
surface has six tools and the sole action is explicit execute-once retrieval.

The final promotion candidate does not ship a scheduler, background refresh, trading,
order routing, model-selected URLs, or model-selected executors.

## Migration and compatibility

Existing schema-1 Watchlists upgrade in place through the governed migration
path; legacy v0.1 Watchlist import remains an explicit compatibility flow.
Historical M5/M8 documents and readonly surfaces are retained for audit, not
as a competing V1 product authority.

## Published RC provenance

The immutable annotated tag `v1.0.0-rc.1` peels to
`2c03b03f0853a509791f755daa0bb8f2be181dca`. The release manifest binds that
exact commit and its Git tree. Documentation status changes after publication
do not move or replace the RC tag.

## Release gate

The published RC passed repository validators, deterministic test
profiles, actual browser E2E, fresh-install and upgrade checks, source-archive
verification, and a Git-tree-bound release manifest. Any later correction that
changes product bytes requires a new RC tag rather than moving `v1.0.0-rc.1`.
The final promotion changes ProductVersion and release-status metadata only;
final `v1.0.0` publication remains separately gated.
