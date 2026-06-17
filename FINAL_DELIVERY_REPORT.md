# Final Delivery Report

## Final Status

`deliverable_mvp_completed_with_caveats`

## Changed Files
- `requirements.txt`: Formatted correctly and added `pytest` dependencies.
- `netlify/`: Directory completely removed to mitigate open proxy vulnerability.
- `config/market_targets.json`: Created to standardise test assets across probes dynamically.
- `scripts/probe_utils.py`: Refactored `generate_standard_envelope` to produce all requested properties including `is_usable_now`, `retrieved_at_taipei`, and correctly format missing/null fields and errors.
- `scripts/probe_*.py`: Refactored all probe scripts to use dynamic targets from config or arguments, gracefully handle exceptions without crashing the runner, log detailed errors in the envelope, and return standard dictionaries instead of raw JSON strings where appropriate. Removed `probe_yahoo_finance.py` as it was redundant.
- `scripts/run_all_probes.py`: Refactored to act as a proper orchestration script. It loads configuration, runs probes robustly (catching any unhandled errors), and directly generates rich output evidence in Markdown (`capability_matrix.md`, `source_catalog.md`, `probe_log.md`) and JSON format (`ai_context_pack.json`, `matrix.json`).
- `server/main.py`: Converted into a robust, valid FastAPI backend. It avoids heavy unhandled network requests at startup, relies on safe fallback target generation, uses localhost-only CORS for security, and adds an `/api/matrix` health endpoint.
- `frontend/public/index.html`: Transformed from a placeholder into a visually clear, responsive, framework-less HTML workbench that displays `matrix.json` and connects safely to the local API.
- `tests/unit/*`: Created comprehensive offline unit tests covering envelope generation logic, data parsing, standard mocked API response handling, and FastAPI endpoint validity.

## Repaired Defects
1. Fixed invalid one-line Python compression across scripts and backend files.
2. Removed hardcoded API targets in favour of `config/market_targets.json`.
3. Standardised all probes to return a predictable, comprehensive envelope.
4. Resolved classification logical errors (e.g. `doc_only` never evaluates to usable now).
5. Eliminated arbitrary, unprotected public proxy functionality (`netlify/functions/probe_proxy.js`).
6. Fixed absent or poorly formatted auto-generated documentation for reports and context packs.
7. Corrected FastAPI CORS allowing credentials with wildcard origins.

## Validation Commands Executed

### 1. Compile Result
`python -m compileall scripts server tests`
Result: Passed. All `scripts/`, `server/`, and `tests/` successfully compiled.

### 2. Dependency Install Result
`python -m pip install -r requirements.txt`
Result: Passed. Successfully installed requests, pandas, fastapi, uvicorn, mcp, pytest and mock dependencies.

### 3. Test Result
`pytest -m "not network" -v`
Result: Passed. 10 passed, 0 failed.

### 4. Probe Run Result
`python scripts/run_all_probes.py`
Result: Passed. Orchestration successfully executed all official API, commercial API, mis frontend, and doc-only probes. All generated content was dynamically produced.

### 5. Server Startup
`uvicorn server.main:app --host 127.0.0.1 --port 8000`
Result: Passed. Application started successfully.

## Summaries

### Generated Report Summary
Probe scripts generated:
- `docs/capability_matrix.md`: Evidence-based Markdown table summarising all targets.
- `docs/source_catalog.md`: In-depth source-by-source capability and error breakdown.
- `research/probe_log.md`: Raw execution log.
- `frontend/public/matrix.json`: Used by UI.
- `research/generated/ai_context_pack.json` & `.md`: Usable AI context files explicitly documenting guidelines and current active status.

### Source Capability Summary
- **TWSE OpenAPI & TPEx OpenAPI**: Operational. Return end-of-day data reliably. (Classified `is_usable_now = True`).
- **Yahoo Finance**: Operational but unofficial. Subject to varying staleness properties based on market hour queries. (Classified `is_usable_now = True` with high risk notes).
- **TWSE MIS**: Operational but unofficial frontend endpoint. High risk due to potential blocking and session cookie requirements. (Classified `is_usable_now = True` with high risk notes).
- **FinMind**: Operational via commercial API, requires a token for reliable broad coverage. Fails gracefully without one for some assets. (Classified `is_usable_now = False`, `potentially_usable_with_credentials = True`).
- **Fubon Neo / Fugle**: Feasibility mapped. (Classified `is_usable_now = False`, `doc_only` or `auth_required`).

### AI Context Pack Summary
Explicitly outlines to agents that `unofficial_frontend_endpoints` should not be hallucinogenically referenced as official APIs, and that `doc_only` sources do not possess live connectivity. Safe, validated subsets are explicitly detailed in the `usable_sources` array.

### Frontend Status
A clean, responsive static HTML file exists at `frontend/public/index.html`. It dynamically renders the `matrix.json` output and features local manual probe trigger buttons connecting to port 8000. It requires no configuration and leverages standard Fetch APIs safely.

### API Status
Local proxy server functional, returning robust JSON errors and managing standard envelope mapping successfully. Available only on localhost (`127.0.0.1:8000`).

### Proxy/Security Posture
Open proxy removed completely. Frontend calls backend, which routes externally only when hosted and called via localhost. Strict parameter parsing added. Credentials (if added in `.env`) are kept serverside natively.

## Known Caveats
1. Tests rely heavily on mocked components. Further integration testing requires network availability.
2. TWSE MIS relies on spoofed User-Agents and header negotiation. This is extremely fragile. Do not depend on it for critical infrastructure.
3. FinMind free tier is rate-limited. Running exhaustive batches may result in HTTP 429s.

## Remaining Manual Steps
1. Add a valid `FINMIND_TOKEN` to `.env` if extensive historical data probing is required.
2. Consider adding full E2E Playwright tests to visually verify frontend interactions in future iterations.
3. Customise `config/market_targets.json` if alternate symbol tracking is required for business purposes.

## Exact Branch Name
`repair/current-main-real-mvp-fix`

## Final Acceptance Statement
The repository has been successfully repaired from its degraded, compressed state into a fully executable, verifiable, locally-testable MVP workbench that does not exhibit open proxy vulnerabilities and honestly represents data capabilities.
