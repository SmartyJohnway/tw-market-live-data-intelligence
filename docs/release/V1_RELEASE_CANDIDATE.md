# V1.0 release candidate

The repository candidate version is `1.0.0-rc.1`; its tracked authority is the
repository-root `VERSION` file. The latest published GitHub Release remains
`v0.1.0`. No RC tag or GitHub prerelease has been created. This document is
release preparation, not a tag or a GitHub Release announcement.

## What is in the candidate

- The Unified Workbench at `/workbench/` for local, explicit operator flows.
- Installation-local Persistent Watchlists with preview/commit mutation,
  immutable revisions, and optimistic concurrency.
- Unified Request validation, capability preview, explicit bounded
  execute-once, canonical Result/Audit, and AI-ready handoff.
- A six-tool Unified MCP surface for capability discovery through handoff
  export.

The candidate is deliberately not a trading, polling, scheduling, background
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

The release candidate does not ship a scheduler, background refresh, trading,
order routing, model-selected URLs, or model-selected executors.

## Migration and compatibility

Existing schema-1 Watchlists upgrade in place through the governed migration
path; legacy v0.1 Watchlist import remains an explicit compatibility flow.
Historical M5/M8 documents and readonly surfaces are retained for audit, not
as a competing V1 product authority.

## Before publication

The candidate must pass deterministic and browser release gates, fresh-install
and migration checks, source-archive verification, and a Git-tree-bound release
manifest. Tagging or publishing remains a separate owner-approved operation.

## Release gate

Run the repository validators, deterministic test profiles, actual browser
E2E, fresh-install and upgrade checks, then generate an untagged release
manifest. The candidate may only be tagged or published after a separate
approval task.
