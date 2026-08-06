# Unified Workbench Mode A: User Guide

Mode A allows an operator to inspect, format, and validate Unified Market Evidence Requests against the M8R-05A F3 canonical validation engine, strictly offline.

## Launching
```bash
python scripts/run_unified_workbench.py
```
Open your browser to the URL printed on the console (must be `127.0.0.1` or `localhost`).
Go to `/workbench/mode-a/UnifiedMarketEvidenceWorkbench.html`

## Capabilities
1. **Load/Paste**: Paste JSON or click "Choose File" to load a local `.json` file containing a Unified Request.
2. **Format**: Beautifies the pasted JSON payload.
3. **Validate**: Submits the payload to the local FastAPI server. The server evaluates it against the Canonical F3 runtime and returns detailed blocking issues, target resolutions, and capability statuses.
4. **Copy/Export**: Download or copy your normalized JSON requests and the deterministic validation reports for future audit.

## Understanding Output
- **Target Status**: Will resolve your requested security (`2330`) into its Canonical Identity. If unsupported, it will show a warning/blocker.
- **Capability Status**: Evaluates whether your requested `data_needs` match current local repository execution boundaries.
- **Blockers**: Things preventing this request from ever moving to execution.
- **Warnings**: Minor issues (e.g. missing optional capabilities).

## What Mode A DOES NOT Do
- It does **not** call any real external APIs or TWSE/TAIFEX sources.
- It does **not** execute the request or generate data.
- It does **not** provide Authorization tokens (Mode B2).
- It will **not** allow you to preview execution if the payload is completely invalid.
