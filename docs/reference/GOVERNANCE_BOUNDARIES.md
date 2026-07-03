# Governance Boundaries

Forbidden in M5R scope and normal local operation: M5F mutation, source semantic changes, contract changes, startup network calls, scheduled polling, full-market scans, `frontend/public` writes, `research/generated` refreshes, production/prod writes, broker/auth credentials, raw payload leakage, and trading outputs including buy/sell/hold, ranking, target price, or recommendation.

Every source-derived artifact must preserve source identity, source time where available, retrieval time, freshness/delay status, caveats, and raw payload policy.

## M6A local frontend compatibility boundary

M6A improves local operator UX only. Opening the readonly workbench via `file://`, a localhost static server, or the FastAPI origin does not start observations, polling, schedulers, startup network calls, source rewrites, or canonical updates. Watchlist slots are in-memory browser state unless the operator exports JSON locally.

## M6B test and source-contract boundary

M6B adds test strategy and manual source-contract checks only. It does not change M5F canonical semantics, M5K/M5L observation semantics, M5Q source-health semantics, or M5N conversation semantics. Live integration checks are manual, bounded to `2330`, `0050`, and `TX`, excluded from default CI with the `network` marker, and must not write M5F, `frontend/public`, `research/generated`, or production paths.

TLS policy was strict-only in M6B. M6D adds explicit compatibility policy controls while preserving strict default behavior; no silent TLS disable or global unverified SSL context is allowed.


## M6D TLS compatibility boundary

M6D implements governed SSL/TLS policy modes for existing bounded live network paths only: `strict`, `compatibility`, and `unsafe-explicit`. Strict remains default and uses normal verified TLS. Compatibility mode is explicit and diagnostic for known Windows/Python 3.13 certificate compatibility failures; it must not claim strict TLS verification. `unsafe-explicit` is explicit only, carries the strongest warning, and may disable TLS verification only for the operator-requested bounded command.

No silent TLS fallback exists. The repository must not globally install an unverified SSL context and must not automatically fallback from strict to unsafe behavior. Do not use unsafe-explicit unless you understand TLS verification is disabled.
