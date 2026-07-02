# Operator Quick Start

```bash
python -m pip install -r requirements.txt
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
python scripts/run_m5q_source_health_probe.py --check-only
python scripts/build_m5n_conversation_context.py
uvicorn server.main:app --host 127.0.0.1 --port 8000
python server/mcp_server.py --startup-check
```

Open `frontend/readonly-preview/M5KLocalAIWorkbench.html` for the readonly workbench. Keep bounded observation manual and explicit only.

## M6A local frontend UX

1. Start the local API only when you want browser access:

   ```bash
   uvicorn server.main:app --host 127.0.0.1 --port 8000
   ```

2. Open `frontend/readonly-preview/M5KLocalAIWorkbench.html` directly or through a localhost static server.
3. Use **Check local API** to confirm connectivity.
4. Use **Load default watchlist**, import/export JSON, duplicate in-memory watchlist slots, and manual history buttons as needed.

The workbench does not auto-execute bounded observation on load. Observation execution remains an explicit Mode B/Mode C action with existing backend guardrails.
