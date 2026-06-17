# AI Vibe Coding Long Task Prompt

You are working on the repository `TW-Market Live Data Intelligence`.

## Mission

Discover, validate, benchmark, and document feasible methods for AI systems to obtain Taiwan equity market information with high freshness, legal safety, reproducibility, and maintainability.

## Do not assume the solution

Do not assume TWSE MIS is the correct answer. Explore every feasible source and architecture.

## Key goals

1. Build a source catalog.
2. Probe candidate sources.
3. Document failures as carefully as successes.
4. Normalize useful data into a common schema.
5. Design an AI-friendly architecture for ChatGPT, Codex, and MCP usage.
6. Recommend a robust long-term approach.

## Candidate sources

- TWSE official website / OpenAPI
- TPEx official website / OpenAPI
- TWSE MIS
- Yahoo Taiwan Finance
- Yahoo Finance global endpoints
- Goodinfo
- FinMind
- Fugle MarketData API
- Fubon Neo API
- Open Securities APIs
- Browser automation
- MCP/local tools

## Constraints

- Do not bypass authentication or access controls.
- Do not use aggressive polling.
- Do not commit secrets.
- Respect legal and ethical constraints.
- Separate official, unofficial, and commercial sources.

## Expected outputs

Update or create useful files only. Avoid empty ornamental files.

Required updates:

- `docs/source_catalog.md`
- `docs/capability_matrix.md`
- `research/probe_log.md`
- `docs/data_contract.md`
- `docs/recommended_architecture.md`

Optional code:

- `scripts/probe_twse_mis.py`
- `scripts/probe_yahoo_finance.py`
- `src/market_data/` adapters

## Definition of success

A future AI assistant should be able to answer Taiwan market questions using verified, reproducible, timestamp-aware data instead of stale search summaries or screenshots.
