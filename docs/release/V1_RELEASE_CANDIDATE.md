# V1 release candidate

The candidate product version is `1.0.0-rc.1`; its tracked authority is the
repository-root `VERSION` file. This document is release preparation, not a
tag or a GitHub Release announcement.

## Installation

```bash
python -m venv .venv
# activate the venv for your shell
python -m pip install -r requirements-lock.txt
python scripts/verify_environment.py
python scripts/manage_security_master.py status
```

Fresh installations correctly report `NOT_INITIALIZED`. An operator may later
run `python scripts/manage_security_master.py update --live`; that is explicit
and bounded, never a startup action.

## Operational contract

Start `python scripts/run_unified_workbench.py` and
`python scripts/run_unified_market_evidence_mcp.py` on loopback. The current
Workbench is `/workbench/`; the legacy Mode-A route redirects to it. The MCP
surface has six tools and the sole action is explicit execute-once retrieval.

The release candidate does not ship a scheduler, background refresh, trading,
order routing, model-selected URLs, or model-selected executors.

## Release gate

Run the repository validators, deterministic test profiles, actual browser
E2E, fresh-install and upgrade checks, then generate an untagged release
manifest. The candidate may only be tagged or published after a separate
approval task.
