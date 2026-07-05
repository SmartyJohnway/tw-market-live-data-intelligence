# Operator Guide

## Fresh clone trial path

1. Clone the repository and install normal dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Run operator readiness:
   ```bash
   python scripts/run_test_profile.py operator-preflight --json
   ```
3. Start the local FastAPI surface:
   ```bash
   uvicorn server.main:app --host 127.0.0.1 --port 8000
   ```
4. Open the readonly frontend:
   ```text
   frontend/readonly-preview/M5KLocalAIWorkbench.html
   ```
5. Use Mode A/B/C interactively. Mode A is M5F canonical context, Mode B is bounded observation/source-health context, and Mode C is the Conversation Package.

## Browser validation

Install browser dependencies only when real browser/operator validation is needed:

```bash
python -m pip install -r requirements-browser-e2e.txt
python -m playwright install --with-deps chromium
python scripts/run_test_profile.py browser-e2e --json
```

## Explicit bounded live validation

Bounded live checks are manual only and never run automatically in normal CI:

```bash
python scripts/run_test_profile.py bounded-live --confirm-bounded-live --ssl-policy compatibility
```

Use `--ssl-policy strict` unless an operator explicitly needs compatibility mode for the known Windows/Python certificate compatibility case. There is no silent TLS fallback.
