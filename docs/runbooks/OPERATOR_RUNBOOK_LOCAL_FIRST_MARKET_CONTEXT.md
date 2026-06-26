# Operator Runbook: Local-First Market Context

## Current Authorization State

This repository is in a local-first governed system state. Operators may run non-network validation and inspect committed readonly artifacts, fixtures, contracts, and reports. No production refresh, generated artifact refresh, frontend artifact refresh, full-market scan, broker/auth activation, or trading signal generation is authorized by this runbook.

## Safe to Run

Safe local validation commands:

```bash
python -m compileall scripts tests
pytest -m "not network"
```

Safe readonly activities:

- Read documentation under `docs/`.
- Read committed test fixtures under `tests/fixtures/`.
- Run unit tests marked as not network.
- Inspect existing committed evidence and generated artifacts as historical/readonly context only.

## Forbidden

Operators must not run:

- live probes without explicit authorization.
- `scripts/run_all_probes.py`.
- full-market scans.
- controlled live probe execution without explicit authorization.
- production refresh.
- generated artifact refresh under `research/generated/*`.
- frontend artifact refresh under `frontend/public/*`.
- broker/auth workflows.
- FinMind, Fugle, or Fubon enablement.
- credential, cookie, token, or `.env` commits.
- buy/sell/hold or trading-signal generation.

## Non-Network Validation Procedure

1. Confirm working tree cleanliness with `git status --short`.
2. Run `python -m compileall scripts tests`.
3. Run `pytest -m "not network"`.
4. Treat warnings as review items, not authorization to run network probes.
5. Do not run tests or commands that require network access unless a later milestone explicitly authorizes them.

## Interpreting Readonly Generated Artifacts

Existing generated artifacts, if present, are readonly historical context. They are not production current market state unless a separately authorized production refresh explicitly says so. Do not infer current prices from stale artifacts, and do not substitute yesterday's close as current market data.

## MCP Boundaries

- MCP-01 readonly context tools are for inspection and readback. They do not authorize live probing or writes.
- MCP-02 explicit controlled live probe tools require explicit operator authorization and must remain bounded by governance flags.
- MCP-03 governed evidence readback is for reading controlled evidence and caveats; it must not promote evidence into production current market state.

## TWSE MIS Normalization v2 Caveats

TWSE MIS normalization v2 preserves source timestamps, retrieval timestamps, `freshness_status`, `delay_status`, `staleness_seconds`, data quality flags, and source risk flags. TWSE MIS remains an unofficial frontend source. `live_candidate` is not a realtime guarantee, and delayed/stale/unknown states must be displayed to downstream AI and UI consumers.

## Not Production-Ready

The system is not production-ready for:

- autonomous refresh to production state.
- frontend current-market publication.
- full-market coverage.
- realtime claims.
- broker execution or authenticated market data.
- commercial API use without credential governance.
- trading recommendations.

## Next Recommended Production-Authorization Ladder

1. Review and merge local-first contracts and fixture coverage.
2. Add a staging-write implementation behind explicit confirmations only after design approval.
3. Validate staging writes with fixtures and non-network tests.
4. Perform one bounded controlled source refresh with explicit authorization and evidence capture.
5. Review freshness, delay, source risk, and legal/maintenance risk findings.
6. Only then consider a separate production-write contract and approval gate.
7. Keep frontend publication as a separate authorization step after production-state governance is approved.
