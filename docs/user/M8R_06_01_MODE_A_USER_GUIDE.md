# Unified Workbench Mode A: User Guide

> [!NOTE]
> **Current Activation Status: ACTIVE (governed local candidate required)**
>
> Production validation loads the committed pointer and immutable seal, then strictly validates the Git-ignored local compact candidate. If that candidate is absent or invalid, the API fails closed with `409 canonical_security_master_unavailable`; fixtures are never a production fallback.

Mode A validates Unified Market Evidence Requests through canonical F3. Mode B1 then projects a deterministic offline Preview through the accepted 05B-01 planner without authorization or execution.

## Launching
```bash
python scripts/run_unified_workbench.py
```
Open your browser to the URL printed on the console (must be `127.0.0.1` or `localhost`).
Go to `/workbench/mode-a/`.

## Capabilities
1. **Load/Paste**: Paste JSON or click "Choose File" to load a local `.json` file containing a Unified Request.
2. **Format**: Beautifies the pasted JSON payload.
3. **Validate**: Submits the payload to the local FastAPI server. The server evaluates it against the Canonical F3 runtime and returns detailed blocking issues, target resolutions, and capability statuses.
4. **Copy/Export**: Download or copy your normalized JSON requests and the deterministic validation reports for future audit.
5. **Build Offline Preview**: After validating the exact current request, inspect planned evidence, coverage, gaps, bounds, and the internal orchestration plan. Editing or replacing the request invalidates the prior validation and Preview.

## Understanding Output
- **Target Status**: Will resolve your requested security (`2330`) into its Canonical Identity. If unsupported, it will show a warning/blocker.
- **Capability Status**: Evaluates whether your requested `data_needs` match current local repository execution boundaries.
- **Blockers**: Things preventing this request from ever moving to execution.
- **Warnings**: Minor issues (e.g. missing optional capabilities).

## What Mode A DOES NOT Do
- It does **not** call any real external APIs or TWSE/TAIFEX sources.
- It does **not** execute the request or generate data.
- Mode B1 does **not** create or consume authorization and does **not** execute network calls.
- It does **not** provide Authorization tokens or Mode B2 controls.
- It will **not** build a target Preview for a request that fails the Unified Request schema.
