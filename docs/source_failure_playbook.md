# Source Failure Playbook

## TWSE OpenAPI malformed or missing rows
Record missing symbol, row shape, status code, retrieval timestamp, and parser error. Preserve last-known-good M5F package. Do not substitute yesterday close as current data.

## TPEx OpenAPI failures
Classify as source failure or unsupported target. Record URL, method, status, body sample, and parsed fields if available. Do not promote partial TPEx data without caveats.

## TWSE MIS block/cookie/rate-limit/session issues
Treat as unofficial browser-rendered endpoint risk. Do not bypass cookies, sessions, or rate limits. Do not use MIS as canonical product refresh without future authorization.

## Yahoo identity and suffix mismatch
Reject suffix-drop, Japan OTC, or name/identity mismatch. Record symbol requested, symbol returned, exchange, timezone, and mismatch reason.

## Stale or delayed data
Display source date, retrieval timestamp, stale/delay status, and caveats. Never relabel stale data as realtime.

## Partial target failure
Keep successful targets descriptive and disclose failed targets separately. Do not fabricate missing symbols.

## Malformed evidence or manifest/hash mismatch
Fail closed. Recompute hashes from immutable upstream artifacts. If mismatch persists, block release and preserve last-known-good package.

## Missing canonical package
FastAPI and MCP must return structured errors. Operators should rebuild in `/tmp`, validate, then write only to the fixed M5F path.

## Consumer disagreement
If frontend/API/MCP symbols, source date, hashes, or caveats diverge, block release. Canonical payload wins; regenerate derivatives from it.

## Last-known-good preservation
Never delete prior validated evidence while investigating. Do not write into M5B/M5C/M5D, `research/generated`, or `frontend/public` during M5FGH repair.
