# M6D Compatibility Hardening: Windows Python 3.13 TLS and Local Networking

## Problem addressed

Windows + Python 3.13 operators may encounter TWSE MIS TLS certificate compatibility failures during explicit bounded live observation. M6D adds governed compatibility controls without weakening repository defaults.

## SSL policy design

Supported modes are `strict`, `compatibility`, and `unsafe-explicit`. CLI `--ssl-policy` overrides `TW_MARKET_SSL_POLICY`, which overrides the default `strict`. Invalid modes fail closed.

## Default strict behavior

Strict remains default everywhere. It uses normal verified TLS, creates no unverified context, and performs no silent fallback.

## Compatibility mode

Compatibility mode is explicit and diagnostic. It is intended for known Windows/Python 3.13 certificate compatibility failures and reports `compatibility_mode_used=true`; it must not claim strict TLS verification.

## Unsafe-explicit mode

`unsafe-explicit` must be requested explicitly and reports `unsafe_mode_used=true`. Do not use unsafe-explicit unless you understand TLS verification is disabled.

## How to use on Windows/Python 3.13

If TWSE MIS TLS fails on Windows/Python 3.13, retry only the explicit bounded live command with compatibility mode:

```bash
python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation --ssl-policy compatibility
```

or:

```bash
python scripts/run_m6b_source_contract_preflight.py --execute-live-contract-check --ssl-policy compatibility
```

## What remains forbidden

No M5F mutation, schema fork, source-health semantic change, conversation semantic change, frontend/public write, research/generated write, production/prod write, broker/auth, orders, polling, scheduler, startup network calls, full-market scan, trading recommendation, ranking, target price, buy/sell/hold output, raw payload leakage, silent TLS disable, or automatic strict-to-unsafe fallback is allowed.

## Local networking/CORS verification

The frontend keeps `file://` API-base fallback to `http://127.0.0.1:8000`, and localhost/127.0.0.1 local API detection remains intact. FastAPI CORS continues to allow `Origin: null`, localhost, and 127.0.0.1 while `allow_credentials` remains `False`. No remote/cloud endpoint is added.

## Tests added

M6D adds tests for strict default behavior, CLI/env precedence, invalid-policy fail-closed behavior, unsafe explicit reporting, strict avoiding unverified contexts, compatibility diagnostics, mocked SSL context delivery to network helpers, M5K/M6B SSL diagnostics, Windows/Python 3.13 operator hints without network, and local CORS compatibility.

## Validation commands

Required validation commands are listed in the task and were run for this PR. Default validations do not perform live network calls.

## Known caveats

Compatibility mode cannot guarantee exchange availability or realtime data. It only addresses selected TLS compatibility behavior for explicit bounded commands. Live compatibility verification remains operator-run unless a bounded manual live check is reported.

## Forbidden behavior confirmation

Strict remains default. Compatibility mode is explicit and diagnostic. No silent TLS fallback exists. Do not use unsafe-explicit unless you understand TLS verification is disabled.
