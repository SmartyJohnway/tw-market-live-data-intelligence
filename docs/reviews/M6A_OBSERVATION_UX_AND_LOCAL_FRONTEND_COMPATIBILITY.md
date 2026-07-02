# M6A Observation UX and Local Frontend Compatibility Review

## What changed

- Added frontend API-base detection for `file://`, localhost static server, `127.0.0.1` static server, and same-origin FastAPI usage.
- Added clear local API unavailable guidance with the command `uvicorn server.main:app --host 127.0.0.1 --port 8000`.
- Added in-memory watchlist slots, import/export, duplicate, and validation-error display UX.
- Added local observation history, comparison, and timeline displays from existing Level 2 artifacts.
- Added source-health history/timeline display from existing Level 2 source-health artifacts.
- Expanded Conversation Package UX reminders and copy/download affordances.
- Added readonly FastAPI summary endpoints for observation history and source-health history.
- Tightened local CORS to localhost/127.0.0.1 origin regex, `GET`/`POST`, and no credentials.

## What did not change

- M5F remains the canonical Level 1 package and is not mutated.
- M5K/M5L observations remain bounded Level 2 context.
- M5Q remains source-health evidence.
- M5N remains the governed Conversation Package handoff path.
- No source adapter semantics, observation semantics, source-health semantics, or Conversation Package builder semantics changed.
- No trading, broker/auth, orders, automatic refresh, polling, scheduler, startup network call, full-market scan, raw endpoint payload exposure, or canonical promotion was added.

## How local frontend API detection works

- `file://` defaults to `http://127.0.0.1:8000`.
- `http://localhost:<non-8000>` and `http://127.0.0.1:<non-8000>` default to `http://127.0.0.1:8000`.
- FastAPI-origin usage on port 8000 uses the same origin.
- The operator can override the visible local API base input for local development.

## CORS policy

FastAPI allows only local HTTP origins matching localhost or 127.0.0.1 with any port. It allows `GET` and `POST`, allows headers, and disables credentials. `file://` is handled in the frontend by targeting the local API base.

## Watchlist import/export UX

The frontend uses the existing watchlist contract. Imported JSON is held in memory, shown in the editable table, validated through the existing backend validation endpoint, and can be exported by the browser. No backend persistence was added.

## Observation history/diff/timeline UX

The workbench can load `/api/m5k/live-observation/history`, display run counts, show latest per-symbol summaries, and compare latest fields to the previous local run when present. The UI labels this as observation comparison only, not a trading signal, and not a current-price guarantee.

## Source health timeline UX

The workbench can load `/api/source-health/history`, display latest/prior source-health run summaries, and preserve the source family, status, freshness, delay, caveats, and recommended next-step fields where available.

## Conversation Package UX

The workbench displays Conversation Package availability through the existing context endpoint and supports JSON/Markdown preview, copy, and download. It reminds operators to keep Level 1 canonical context separate from Level 2 observations/source-health context and excludes raw endpoint payloads.

## Known caveats

- SSL compatibility policy was not implemented in M6A. Strict TLS remains the only implemented behavior; explicit compatibility/unsafe policies should be handled in a future safe task if needed.
- History quality depends on local artifact availability. A single artifact yields a one-point timeline.
- Watchlist slots are browser memory only; export JSON if the operator wants to preserve them.

## Validation commands

```bash
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
python scripts/run_m5k_postmerge_validation.py --check-only
python scripts/run_m5q_source_health_probe.py --check-only
python scripts/build_m5n_conversation_context.py
python scripts/governance_forbidden_path_guard.py
python scripts/forbidden_behavior_scanner.py
python server/mcp_server.py --startup-check
git diff --check
```

## Forbidden behavior confirmation

Confirmed: no M5F mutation, no contract/schema fork, no observation semantic change, no source-health semantic change, no conversation semantic change, no `frontend/public` write, no `research/generated` write, no `production/prod` write, no broker/auth, no polling/scheduler/startup network calls, no full-market scan, no trading output, no raw payload leakage, and no silent TLS disable.
