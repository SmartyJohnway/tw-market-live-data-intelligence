# Mode A/B/C Walkthrough

The current Mode A/B/C model is the Unified Market Evidence flow.

## Mode A — Validate / resolve identity

Input: a Unified Market Evidence Request.

Mode A:

- validates the request schema;
- resolves canonical target identity through the installation-local Security
  Master;
- validates capability/target scope;
- performs no market execution.

A fresh installation may fail closed with
`SECURITY_MASTER_NOT_INITIALIZED`.

## Mode B1 — Preview

Preview computes the deterministic orchestration plan:

- exact targets;
- requested capabilities;
- selected governed route/executor;
- operation/network bounds;
- blocked/omitted operations;
- plan identity/hash.

Preview performs no authorization and no market network request.

## Mode B2 — Authorize / execute once

Authorization binds the approved plan. Execution then consumes that
authorization through the fixed execute-once boundary.

```text
Preview != Authorization != Execution
```

A second use of a consumed authorization must fail closed.

## Mode C — Result / Audit / AI Handoff

After final execution:

- canonical Result is built/verified;
- separate Audit Package preserves execution/provenance detail;
- AI Handoff exports verified AI-safe evidence and citation references;
- Mode C does not perform another market fetch.

V3 is the preferred current Request/Result/Audit authority. Persisted historical
V1/V2/V3 packages retain their stored version.

## Workbench

```bash
python scripts/run_unified_workbench.py
```

Open `http://127.0.0.1:8000/workbench/`.

## Current Phase H note

V3 promotion does not imply complete interpretation coverage. The only active
Phase H route is currently TPEx attention; broader H1/H2/H3 routes remain
uncovered, blocked, plan-only or inactive according to current route authority.
