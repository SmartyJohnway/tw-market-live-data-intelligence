# Governance Boundaries

Forbidden in M5R scope and normal local operation: M5F mutation, source semantic changes, contract changes, startup network calls, scheduled polling, full-market scans, `frontend/public` writes, `research/generated` refreshes, production/prod writes, broker/auth credentials, raw payload leakage, and trading outputs including buy/sell/hold, ranking, target price, or recommendation.

Every source-derived artifact must preserve source identity, source time where available, retrieval time, freshness/delay status, caveats, and raw payload policy.
