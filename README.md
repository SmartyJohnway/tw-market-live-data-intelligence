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

## Known Caveats
1. Unofficial endpoints (like TWSE MIS or Yahoo Finance) are extremely fragile. They are rate-limited, require specific headers (sometimes cookies), and can break without notice.
2. The concept of "real-time" is strictly bound by the `delay_status` and `staleness_seconds` metrics defined in the data contract envelope. Do not assume data is live unless explicitly proven by these fields.

## Current Status
`deliverable_mvp_completed_with_caveats` - The MVP framework is operational, heavily documented, tested offline, and generates dynamic evidence-based reports natively.