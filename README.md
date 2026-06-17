# TW-Market Live Data Intelligence Workbench

An AI-native research project and workbench for discovering, validating, benchmarking, and documenting feasible methods for AI systems to access Taiwan equity market information with high freshness, legal safety, reproducibility, and maintainability.

## Mission

Build a framework that enables AI agents to reliably access near real-time Taiwan market information through legally available interfaces. This repository evaluates various methods: TWSE MIS, Yahoo Finance, Fugle, FinMind, TWSE/TPEx OpenAPI.

## Features & Outcomes
- **Evidence-Based Market Data**: Discovers and probes market data sources reliably.
- **Data Source Capability Matrix**: Maintains accurate status records of available data capabilities, explicitly distinguishing unsupported asset classes.
- **AI Context Pack**: Provides AI-ready `json` and `md` summaries of data availability, freshness, and risks.
- **Local API Layer**: A safe, local-first FastAPI service to run live probes easily.
- **Workbench Frontend**: A simple HTML interface for visually inspecting source matrices and testing probes.
- **Configuration-Driven**: Supports a target list of stocks, ETFs, Indices via `config/market_targets.json`.

## Quick Start & Installation

### 1. Set Up Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Probes & Generate Reports
```bash
python3 scripts/run_all_probes.py
```
*This command runs safely bounded queries against official and unofficial sources, generating the AI Context Pack in `research/generated/` and updating the Capability Matrix in `docs/`.*

### 3. Start the API & Frontend
Run the minimal FastAPI service locally:
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000
```
Open `frontend/public/index.html` in your browser to view the capability matrix and test live API endpoints safely.

## Testing & Validation
This project utilizes `pytest`. Network tests are isolated from offline validation.
```bash
# Run all tests (including network probes)
pytest -v

# Run only offline tests
pytest -m "not network" -v
```

## Security & Constraints
- **Secrets Management**: Do not hardcode API keys or credentials. Use environment variables (e.g., `FINMIND_TOKEN`).
- **No Open Proxies**: Unsafe arbitrary fetch logic has been removed. The proxy functions are strictly disabled to prioritize security.
- **Rate Limiting & Safety**: The probe framework explicitly bounds requests to avoid abusive polling.

## Final Deliverable State
This repository has reached the **Deliverable MVP** stage. Please read `FINAL_DELIVERY_REPORT.md` for a complete status overview.