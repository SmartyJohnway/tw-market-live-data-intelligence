# M3F Frontend Static Serving Guide

This guide explains how to open the local static frontend viewer for the TW-Market Data Intelligence Workbench and how to troubleshoot common issues related to loading generated context artifacts.

## Recommended Local Serving Command

To correctly serve the read-only static viewer, start a local HTTP server **from the root of the repository**:

```bash
python -m http.server 8000
```

## Recommended URL

Once the server is running, open the following URL in your web browser:

[http://localhost:8000/frontend/public/market-context.html](http://localhost:8000/frontend/public/market-context.html)

## Why `file://` Paths May Fail

You should avoid opening the `market-context.html` file directly using your browser's file explorer (which results in a URL starting with `file://`).

The frontend viewer uses the native `fetch()` API to load the generated JSON and Markdown artifacts. Modern browsers impose strict Cross-Origin Resource Sharing (CORS) and security policies on `file://` paths. Because the artifacts are located in a parent directory relative to the frontend files (`../../research/generated/`), `fetch()` cannot reliably load them outside of an HTTP server environment.

The server must be started from the repository root because the HTTP server sets the root directory as the web root, allowing the relative paths to resolve correctly within the served structure.

## Expected Artifact Paths

The viewer attempts to load the following pre-generated AI artifacts:

- **AI Context Pack:**
  - Relative fetch path: `../../research/generated/ai_context_pack.json`
  - Repo-root path: `research/generated/ai_context_pack.json`
- **ChatGPT Briefing:**
  - Relative fetch path: `../../research/generated/chatgpt_briefing.md`
  - Repo-root path: `research/generated/chatgpt_briefing.md`

## Expected Degraded State

This is a local static viewer evaluating locally generated offline state. As such, you may frequently observe a "Degraded State" banner. This occurs if the system is relying on offline fallback data or if network probes failed to reach the upstream data sources during the generation of the snapshot.

In this degraded state, it is expected that:
- The snapshot may show **0 successful symbols**.
- The snapshot may show that **all targeted symbols failed**.
- The **Failed Sources** and **Failed Targets** tables will remain visible and detail the specific errors or offline statuses.

This behavior is expected and must remain visible; the viewer should not mask or hide these failures.

## Important Disclaimer

This frontend viewer is strictly an AI research workbench artifact viewer. It is **not**:
- A live quote board
- A market dashboard
- Investment advice
- Full-market coverage
- A trading signal UI
- A recommendation engine
- A trading dashboard

Observations provided in the UI are descriptive only and are not trading signals. No official realtime quote guarantee is established.
