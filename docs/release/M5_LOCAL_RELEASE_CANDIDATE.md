# M5 Local Release Candidate

## What is ready

Local validation, M5F canonical package consumption, readonly FastAPI/frontend/MCP operation, manual bounded observation, M5Q source-health checks, and M5N Conversation Package handoff.

## What is not ready

Production deployment, realtime guarantee, broker/auth integration, automatic ordering, scheduled polling, full-market scans, trading recommendations, ranking, target prices, or buy/sell/hold outputs.

## Known caveats

M5F is historical; Level 2 observation is temporary and source-dependent; browser endpoints may be fragile; source-health status is only valid at retrieval time.

## How to run

```bash
python -m pip install -r requirements.txt
uvicorn server.main:app --host 127.0.0.1 --port 8000
python server/mcp_server.py --startup-check
```

## How to validate

Run the checklist commands in [Release Checklist](RELEASE_CHECKLIST.md).

## How to use Mode A/B/C

Use [Mode A/B/C Walkthrough](../operator/MODE_ABC_WALKTHROUGH.md).

## How to verify release status

Confirm [M5XR acceptance evidence](../reviews/M5XR_FINAL_MODE_ABC_LEVEL12_RELEASE_ACCEPTANCE.md), this M5R documentation audit, and a clean forbidden path scan.

## M6E release preflight

M6E adds an operator-facing acceptance report: `python scripts/run_m6e_operator_acceptance.py --check-only`. Treat `pass` as ready, `pass_with_caveats` as ready with documented operator caveats, and `fail` as not release-preflight ready.
