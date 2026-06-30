# Source Matrix

| Source | Role | Level | Mode | Used for | Authority status | Realtime status | Known caveats | Default product usage |
|---|---|---:|---|---|---|---|---|---|
| TWSE_OpenAPI | Official reference source | 1/2 | A/B | Reviewed package evidence, reference checks | Official public API | Not realtime guaranteed | Often EOD/reference semantics; verify source timestamp | Canonical evidence and safe checks |
| TWSE_MIS | Browser JSON observation candidate | 2 | B | Bounded listed-equity observation | Unofficial/browser endpoint | Not realtime guaranteed | Fragile fields/session behavior; can be stale or closed-session | Manual bounded observation only |
| TAIFEX_MIS | Browser JSON observation candidate | 2 | B | Bounded futures observation | Unofficial/browser endpoint | Not realtime guaranteed | Session/freshness semantics need caveats | Manual bounded observation only |
| TPEx / OTC through TWSE_MIS if applicable | OTC route candidate | 2 | B | Bounded OTC observation where route resolves | Route-dependent | Not realtime guaranteed | Coverage and field semantics must be verified per target | Observation candidate, not canonical |
| M5F Canonical Package | Reviewed local context package | 1 | A/C | Baseline context, FastAPI, MCP, frontend, AI handoff | Internal reviewed artifact | Historical/stale, not current | Must not be silently refreshed or mutated | Default baseline |
| M5K latest observation | Temporary bounded observation | 2 | B/C | Latest local observation state | Internal derived artifact | Observation-time only, not guaranteed realtime | Non-canonical; depends on manual execution | Optional temporary context |
| M5Q source health | Manual source-health regression report | 2 | B/C | Source usability health | Internal derived artifact | Status at retrieval only | Not a scanner; no raw payload leakage | Operator diagnostics |
| M5N conversation package | AI handoff package | 1/2 | C | AI discussion context | Internal derived artifact | Derived; inherits caveats | Must not be interpreted as trading advice | AI handoff |
| Licensed vendor future candidate | Future source candidate | TBD | TBD | Potential production-grade data | Commercial/licensed | Unknown until contracted | Requires credentials, terms, governance, and tests | Not default |
