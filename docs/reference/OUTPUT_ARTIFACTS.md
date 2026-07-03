# Output Artifacts

| Artifact | Path | Producer command | Consumer | Network behavior | Write behavior | Canonical or temporary | Raw payload policy |
|---|---|---|---|---|---|---|---|
| M5F canonical package | `research/staging/m5f/m5f_canonical_market_context_01/` | `python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01` | FastAPI, MCP, frontend, AI | None for validation | Reads existing package | Canonical Level 1 | Raw payloads excluded from product docs |
| M5K latest observation | `research/live_observation_runs/m5k/latest_observation.json` | `python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation` | Mode B/C operator review | Explicit manual bounded network | Writes Level 2 observation artifacts | Temporary Level 2 | Raw endpoint payload excluded/minimized |
| M5Q source health | `research/live_observation_runs/source_health/` | `python scripts/run_m5q_source_health_probe.py --execute-health-probe` | Source Health Guide, M5N | Explicit manual bounded network; check-only has none | Writes source-health reports on execute | Temporary Level 2 | Raw endpoint payload excluded |
| M5N conversation context | Local M5N conversation output from builder | `python scripts/build_m5n_conversation_context.py` | AI chat handoff | None | Writes/updates local conversation context artifact | Derived temporary handoff | Summaries only with caveats |
| M5XR acceptance evidence | `docs/reviews/M5XR_FINAL_MODE_ABC_LEVEL12_RELEASE_ACCEPTANCE.md` | Maintainer review evidence | Release verification | None | Documentation only | Release evidence | No raw payloads |
| FastAPI outputs | `server/main.py` responses | `uvicorn server.main:app --host 127.0.0.1 --port 8000` | Frontend/operator | Startup none; explicit endpoints only on command | Local responses; no product artifact writes except explicit bounded execution | Mixed Level 1/2 | Contracts expose caveats |
| MCP outputs | `server/mcp_server.py` tool responses | `python server/mcp_server.py` | MCP clients/AI | Startup none; explicit bounded tool only on confirmation | Tool responses; explicit bounded tool can write Level 2 | Mixed Level 1/2 | JSON/Markdown summaries |
| Frontend readonly workbench | `frontend/readonly-preview/M5KLocalAIWorkbench.html` | Open local file or static server | Operator | Calls local API if configured | No `frontend/public` writes | UI consumer | Displays caveats/status |

## M6A frontend-read summaries

The M6A workbench reads, but does not create, observation history and source-health history summaries from existing local Level 2 artifacts. These summaries are derived from `research/live_observation_runs/m5k/*.json` and `research/live_observation_runs/source_health/*.json`, exclude raw endpoint payloads, and remain non-canonical temporary context.

## M6B source-contract artifact

| Artifact | Path | Producer command | Consumer | Network behavior | Write behavior | Canonical or temporary | Raw payload policy |
|---|---|---|---|---|---|---|---|
| M6B source-contract preflight summary | `research/live_observation_runs/m6b_source_contract/latest_summary.json` | `python scripts/run_m6b_source_contract_preflight.py --execute-live-contract-check` | Release operator diagnostics | Explicit manual bounded network only | Writes only after explicit execution | Temporary Level 2 diagnostic | Raw endpoint payload excluded |

`python scripts/run_m6b_source_contract_preflight.py --check-only` prints the planned contract report, performs no network calls, and writes nothing.


## M6D SSL/TLS diagnostics in artifacts

Explicit M5K live observation outputs and M6B source-contract execute outputs include SSL diagnostics: `ssl_policy`, `tls_verification_mode`, `strict_default`, `compatibility_mode_used`, `unsafe_mode_used`, `silent_tls_fallback=false`, and `network_calls_may_have_occurred`. Check-only outputs may report the selected/default policy for operator clarity but do not imply network execution. Strict remains default, compatibility is explicit and diagnostic, and unsafe-explicit must not be used unless the operator understands TLS verification is disabled.

## M6E operator acceptance artifact

| Artifact | Path | Producer command | Consumer | Network behavior | Write behavior | Canonical or temporary | Raw payload policy |
|---|---|---|---|---|---|---|---|
| M6E operator acceptance report | `research/live_observation_runs/m6e_operator_acceptance/` | `python scripts/run_m6e_operator_acceptance.py --check-only` | Operators/release reviewers | None in check-only | Writes only M6E report JSON/Markdown | Temporary release evidence | Raw endpoint payload excluded |
