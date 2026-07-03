# Governance Boundaries

Forbidden in M5R scope and normal local operation: M5F mutation, source semantic changes, contract changes, startup network calls, scheduled polling, full-market scans, `frontend/public` writes, `research/generated` refreshes, production/prod writes, broker/auth credentials, raw payload leakage, and trading outputs including buy/sell/hold, ranking, target price, or recommendation.

Every source-derived artifact must preserve source identity, source time where available, retrieval time, freshness/delay status, caveats, and raw payload policy.

## M6A local frontend compatibility boundary

M6A improves local operator UX only. Opening the readonly workbench via `file://`, a localhost static server, or the FastAPI origin does not start observations, polling, schedulers, startup network calls, source rewrites, or canonical updates. Watchlist slots are in-memory browser state unless the operator exports JSON locally.
