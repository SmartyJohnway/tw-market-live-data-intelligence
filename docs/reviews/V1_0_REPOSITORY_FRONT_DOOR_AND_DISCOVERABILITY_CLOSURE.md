# V1.0 repository front door and discoverability closure

## Decision

`READY_FOR_V1_RC1_FRONT_DOOR_DISCOVERABILITY_REVIEW`

The Gate B candidate was validated at code commit
`44a9d09cae4b0ec13dffa0ba92a7a8aaf5ebb161` and tree
`514ea148bb63676dd14c8bbb61ae638b159b81d8`. The earlier `39200d56…` validation
subject is superseded by this public-history and security-reporting correction.
This closure records an
evidence-only finalization; it does not authorize an RC tag, GitHub prerelease,
final release, Phase G, or external market execution.

## Public entry points

- Root README and `README.zh-TW.md` identify the candidate as `1.0.0-rc.1`,
  distinguish it from published `v0.1.0`, and provide fresh-install commands.
- The canonical browser surface is `/workbench/` via
  `python scripts/run_unified_workbench.py`; the canonical MCP launcher is
  `python scripts/run_unified_market_evidence_mcp.py`.
- The public workflow shows Watchlist `2330` → validation → preview → explicit
  authorization/one bounded execution → Result/Audit/AI handoff.
- `docs/assets/workbench-overview.png` is an actual Chromium capture using
  deterministic local fixture data. It shows `ready_for_confirmation`, no
  authorization, and no executed market network request.
- Root README contains only the current product front door. Historical
  M5/M6/M8 material remains available through Project History, the
  documentation history/protocol archive, and `docs/archive/`, rather than
  competing with current V1 authority.
- English and Traditional Chinese README files have reciprocal top-level
  language selectors. Security reporting uses an available GitHub private
  channel only when it is visibly enabled; otherwise it asks for a minimal
  public request for a private contact path.

## Community and distribution readiness

`CONTRIBUTING.md`, `SECURITY.md`, issue forms, a social-preview specification,
and an MCP registry-readiness note provide the public collaboration boundary.
No GitHub repository metadata was mutated. The JSON closure retains observed
current topics plus a search-oriented proposed description/topics for owner
review.

## Release-manifest portability correction

Gate A runtime/product validation remains `RC1_POST_MERGE_VALIDATED`. During
owner evidence review we found
`RELEASE_MANIFEST_ARTIFACT_HASH_PORTABILITY_DEFECT`: release artifact hashes
were computed from host checkout bytes. The builder now binds governed artifacts
to exact `HEAD:path` Git blob bytes, fails closed for missing/untracked or dirty
governed artifacts, and has focused tests. This is release-integrity tooling,
not a runtime, public API, MCP, Watchlist, or market-execution change.

## Exact clean-clone validation

A new `git clone --no-local` installation checked out the exact candidate,
installed `requirements-lock.txt` plus the browser E2E extra, passed `pip
check`, and remained clean before and after validation.

| Gate | Result |
| --- | --- |
| Environment, version, public contracts, hygiene | PASS |
| Portable catalog and runtime/Skill/Guide semantics | PASS |
| Both Skill validators | PASS (Security Master: 201 checks) |
| Compileall and JavaScript syntax | PASS |
| Default CI | PASS: 951 passed, 0 failed, 4 skipped |
| Full current non-network | PASS: 2412 passed, 0 failed, 16 skipped |
| Operator preflight and actual Playwright browser E2E | PASS |
| Git-tree-bound release manifest and source archive without `.git` | PASS |

No external market network was used; no production Security Master or Watchlist
state was changed.
