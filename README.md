# TW-Market Live Data Intelligence

An AI-native research project and operational workbench for discovering, validating, benchmarking, and documenting feasible methods for AI systems to access Taiwan equity market information safely and reliably.

## Project Purpose

This repository provides a testable, reproducible workbench to evaluate various data sources for Taiwan equities (TWSE, TPEx, ETFs, futures, etc.). It determines whether sources are live, delayed, stale, or require authentication, and maps their capabilities into a standardized "data contract" suitable for AI Agents.

## What this project is NOT

- It is **not** a high-frequency trading engine.
- It is **not** an open, public proxy for bypassing CORS or rate limits.
- It is **not** a production-ready data feed for commercial applications.

## Quick Start & Installation

### Requirements
- Python 3.10+
- `pip`

### Setup
```bash
# Clone the repository
git clone https://github.com/SmartyJohnway/tw-market-live-data-intelligence.git
cd tw-market-live-data-intelligence

# Install dependencies
python -m pip install -r requirements.txt
```

### Running Tests (Offline)
The repository includes offline unit tests that mock network responses to ensure parsing and envelope generation logic remains intact.

```bash
pytest -m "not network" -v
```

### Report Generation (Network Probes)
To run the automated probe framework against all defined targets in `config/market_targets.json` and generate capability reports:

```bash
python scripts/run_all_probes.py
```
*This will generate rich Markdown documentation in `docs/` and `research/`, and JSON matrix data in `frontend/public/`.*

### Local API Usage (Optional)
A local FastAPI server can be spun up to expose probe endpoints for local frontend or MCP integration.

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

### Frontend Usage
The frontend provides a clear UI to view the generated capability matrix and interact with the local API.
1. Run the local API (`uvicorn server.main:app ...`)
2. Open `frontend/public/index.html` in your browser.

## Safety Notes & Security Posture
- **No Open Proxies:** Previous iterations contained serverless proxies. These have been removed. The frontend now interfaces directly with a locally hosted backend on `127.0.0.1`.
- **No Netlify / Pass-through Functions:** The deployment no longer requires or supports Netlify edge functions or serverless pass-through proxy architecture. All local network routing is explicitly restricted to `127.0.0.1`.
- **Secrets Management:** Do not commit API keys. If utilizing commercial APIs (like FinMind), populate a local `.env` file with `FINMIND_TOKEN=<your_token>`.

## Documentation & Protocols
The system relies heavily on established protocols and taxonomy documentation to accurately categorize assets and data sources. Please refer to the following documents for comprehensive details:

- **Target Taxonomy & Configuration:**
  - [Target Taxonomy](docs/protocol/TARGET_TAXONOMY.md): Defines the canonical asset classes supported by the project.
  - [Target Config Schema Draft](docs/protocol/TARGET_CONFIG_SCHEMA_DRAFT.md): Proposed future structure for `config/market_targets.json`.
- **Symbols & Capabilities:**
  - [Symbol Format Registry](docs/protocol/SYMBOL_FORMAT_REGISTRY.md): Rules for translating internal taxonomy to source-specific formats.
  - [Support Status Semantics](docs/protocol/SUPPORT_STATUS_SEMANTICS.md): Strict definitions for capability matrix statuses (e.g., `supported_observed`, `doc_only`).
  - [Source Target Support Matrix](docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md): Detailed capability matrix cross-referencing sources against target classes.
- **Source Specific Protocols:**
  - [TWSE MIS Protocol](docs/protocol/TWSE_MIS_PROTOCOL.md) & [Dictionary](docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md)
  - [Yahoo Finance Protocol](docs/protocol/YAHOO_FINANCE_CHART_PROTOCOL.md) & [Coverage](docs/protocol/YAHOO_FINANCE_SYMBOL_COVERAGE.md)
  - [TWSE OpenAPI Protocol](docs/protocol/TWSE_OPENAPI_PROTOCOL.md) & [Dictionary](docs/protocol/TWSE_OPENAPI_FIELD_DICTIONARY.md)
  - [TPEx OpenAPI Protocol](docs/protocol/TPEX_OPENAPI_PROTOCOL.md) & [Dictionary](docs/protocol/TPEX_OPENAPI_FIELD_DICTIONARY.md)
  - [Official OpenAPI Source Semantics](docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md)

- **M2 Source-Contract Baseline:**
  - [M2 Source-Contract Baseline](docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md)
  - [M2 Normalized Schema Inventory](docs/protocol/M2_NORMALIZED_SCHEMA_INVENTORY.md)
  - [M3 Readiness Gate](docs/protocol/M3_READINESS_GATE.md)
  - [M2 Closure Review](docs/reviews/M2_CLOSURE_01_SOURCE_CONTRACT_BASELINE_AND_M3_READINESS.md)

- **M3 AI Context Pack Design:**
  - [M3 AI Context Pack Contract](docs/protocol/M3_AI_CONTEXT_PACK_CONTRACT.md)
  - [M3 AI Context Pack Section Schema](docs/protocol/M3_AI_CONTEXT_PACK_SECTION_SCHEMA.md)
  - [M3 AI Context Guardrails](docs/protocol/M3_AI_CONTEXT_GUARDRAILS.md)
  - [M3 AI Context Pack Generator Requirements](docs/protocol/M3_AI_CONTEXT_PACK_GENERATOR_REQUIREMENTS.md)
  - [M3-01 AI Market Context Pack Design Review](docs/reviews/M3_01_AI_MARKET_CONTEXT_PACK_DESIGN.md)

- **M3B AI Context Pack v2 Contract:**
  - [M3 AI Context Pack v2 Contract](docs/protocol/M3_AI_CONTEXT_PACK_V2_CONTRACT.md)
  - [M3 AI Context Pack v2 Section Schema](docs/protocol/M3_AI_CONTEXT_PACK_V2_SECTION_SCHEMA.md)
  - [M3 AI Context Pack v2 Policy](docs/protocol/M3_AI_CONTEXT_PACK_V2_POLICY.md)
  - [M3 AI Context Pack v2 Generator Requirements](docs/protocol/M3_AI_CONTEXT_PACK_V2_GENERATOR_REQUIREMENTS.md)
  - [M3B-01 Completion Report](docs/reviews/M3B_01_AI_CONTEXT_PACK_V2_CONTRACT.md)
  - [M3B-02 Completion Report](docs/reviews/M3B_02_AI_CONTEXT_PACK_V2_GENERATOR.md)
  - An offline generator script exists at `scripts/generate_ai_context_pack.py` to synthesize AI-readable contexts into `research/generated/ai_context_pack.json` and `.md`.
- `scripts/generate_chatgpt_briefing.py`: M3C-02 Offline ChatGPT Briefing Generator.

- **M3 Latest Market Snapshot Design & Generator:**
  - [Latest Market Snapshot Contract](docs/contracts/latest_market_snapshot_contract.md)
  - [Source Priority & Freshness Policy](docs/protocol/LATEST_MARKET_SNAPSHOT_SOURCE_PRIORITY_AND_FRESHNESS_POLICY.md)
  - [Market Session Status Semantics](docs/protocol/MARKET_SESSION_STATUS_SEMANTICS.md)
  - [Latest Market Snapshot Generator Requirements](docs/protocol/LATEST_MARKET_SNAPSHOT_GENERATOR_REQUIREMENTS.md)
  - [M3A-01 Completion Report](docs/reviews/M3A_01_LATEST_MARKET_SNAPSHOT_CONTRACT_AND_GENERATOR_DESIGN.md)
  - [M3A-02 Completion Report](docs/reviews/M3A_02_LATEST_MARKET_SNAPSHOT_GENERATOR.md)
  - A bounded snapshot generator script exists at `scripts/generate_latest_market_snapshot.py` which strictly executes in offline mode to generate `research/generated/latest_market_snapshot.json`.

- **M3C ChatGPT Briefing Contract:**
  - [ChatGPT Briefing Contract](docs/protocol/CHATGPT_BRIEFING_CONTRACT.md)
  - [ChatGPT Briefing Section Schema](docs/protocol/CHATGPT_BRIEFING_SECTION_SCHEMA.md)
  - [ChatGPT Briefing Policy](docs/protocol/CHATGPT_BRIEFING_POLICY.md)
  - [ChatGPT Briefing Generator Requirements](docs/protocol/CHATGPT_BRIEFING_GENERATOR_REQUIREMENTS.md)
  - [M3C-01 Completion Report](docs/reviews/M3C_01_CHATGPT_BRIEFING_CONTRACT.md)

- **M3D Watchlist Observation Semantics:**
  - [Watchlist Observation Semantics](docs/protocol/WATCHLIST_OBSERVATION_SEMANTICS.md)
  - [M3D-01 Completion Report](docs/reviews/M3D_01_WATCHLIST_OBSERVATION_SEMANTICS.md)
  - A watchlist observation generator script exists at `scripts/generate_watchlist_observations.py` which processes `latest_market_snapshot.json` to generate AI-readable observations in `research/generated/watchlist_observations.json`.

- **M3E Frontend Market Context:**
  - [Frontend Market Context Input Contract](docs/protocol/M3E_FRONTEND_MARKET_CONTEXT_INPUT_CONTRACT.md)
  - [Frontend Caveat Register](docs/protocol/M3E_FRONTEND_CAVEAT_REGISTER.md)
  - [Frontend Display Rules](docs/protocol/M3E_FRONTEND_DISPLAY_RULES.md)
  - [M3E-01 Preflight Readiness Report](docs/reviews/M3E_PREFLIGHT_01_FRONTEND_MARKET_CONTEXT_READINESS.md)
  - [M3E-01 Frontend Market Context View Design](docs/design/M3E_01_FRONTEND_MARKET_CONTEXT_VIEW_DESIGN.md)
  - [M3E-03 Final Review and Merge](docs/reviews/M3E_03_FRONTEND_FINAL_REVIEW_AND_MERGE.md)

- **M3F Frontend Usability:**
  - [M3F Frontend Static Serving Guide](docs/protocol/M3F_FRONTEND_STATIC_SERVING_GUIDE.md)
  - [M3F-01 Completion Report](docs/reviews/M3F_01_FRONTEND_USABILITY_STATIC_SERVING_AND_DOCS_HARDENING.md)

## Frontend Static Serving

```bash
python -m http.server 8000
```

Open:
```text
http://localhost:8000/frontend/public/market-context.html
```

## Known Caveats
1. Unofficial endpoints (like TWSE MIS or Yahoo Finance) are extremely fragile. They are rate-limited, require specific headers (sometimes cookies), and can break without notice.
2. The concept of "real-time" is strictly bound by the `delay_status` and `staleness_seconds` metrics defined in the data contract envelope. Do not assume data is live unless explicitly proven by these fields.

## Current Status
`deliverable_mvp_completed_with_caveats` - The MVP framework is operational, heavily documented, tested offline, and generates dynamic evidence-based reports natively.