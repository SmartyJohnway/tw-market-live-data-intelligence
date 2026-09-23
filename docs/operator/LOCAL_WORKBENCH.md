# Local Unified Workbench

The canonical operator surface is the local Unified Workbench:

```bash
python scripts/run_unified_workbench.py
```

Open `http://127.0.0.1:8000/workbench/`.

## Product model

The Workbench uses the same current contract/runtime as Local Service and MCP:

```text
Mode A — Validate / resolve identity
Mode B — Preview / authorize / execute once
Mode C — Result / Audit / AI Handoff
```

The old M5F/M5K/M5N operator model remains historical engineering provenance; it
is not the current operator contract.

## Request composition

The primary Watchlist builder emits the current preferred V3 selection/request
path. Advanced JSON remains available for explicit contract-level work.

Accepted Unified Requests:

- V1
- V2
- V3

V3 is preferred. Explicit V1/V2 requests retain compatibility behavior.

## Persistent Watchlists

Watchlists are installation-local durable state:

- ISIN durable identity;
- immutable revisions;
- optimistic concurrency;
- preview -> commit mutation;
- no silent conversation persistence;
- no silent identity migration.

Watchlist mutation and market evidence execution are separate authorization
domains.

## Identity boundary

The installation-local Security Master is the Taiwan Market Identity Service.

`NOT_INITIALIZED` is a legal fresh-install state. If identity authority is
required but unavailable, the operation fails closed.

## Evidence execution

A request may execute only when current Catalog/Route/Executor authority says
the requested target/capability route is executable.

Preview does not authorize network execution.

Current Phase H execution is incremental: TPEx attention is active; broader H1,
H2, and H3 coverage must not be inferred.

## AI handoff

Mode C produces the canonical Result, separate Audit package, and AI-ready
handoff without issuing an extra market fetch.

New materializations default to V3. Historical persisted V1/V2/V3 packages
remain readable under their stored version.

## Diagnostics

```bash
python scripts/verify_environment.py
python scripts/run_environment_diagnostics.py
python scripts/manage_security_master.py status
```

For regression validation use:

```bash
python scripts/run_test_profile.py default-ci
```

## Network boundary

Default startup and deterministic CI are non-network. Live source access occurs
only inside an explicitly authorized bounded execution. Do not schedule or poll
the Workbench as a substitute for a future governed monitoring contract.
