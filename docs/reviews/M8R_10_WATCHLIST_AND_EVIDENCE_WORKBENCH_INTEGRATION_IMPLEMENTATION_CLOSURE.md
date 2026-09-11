# M8R-10 Watchlist and Evidence Workbench Integration — Implementation Closure

## Decision

M8R-10 and Phase F are closed on validated code commit
`7a9a0546ad1bc03b9f187f9dbfe8acac7d5ac41a` (tree
`ea1414b4b8cbe07518303b4a9c0afccf3cf47aba`).  That commit was pushed before
validation and is reachable from the PR branch.  This finalization changes only
these closure records and the Roadmap.

Principal decision:
`M8R_10_CLOSED_PHASE_F_CLOSED_READY_FOR_V1_RELEASE_READINESS`.

## Product boundary closed

The plain HTML/CSS/JavaScript Workbench under `frontend/unified-workbench/` is
the sole canonical product surface at `/workbench/`; `/workbench/mode-a/`
remains a same-origin compatibility redirect.  M8R-09 SQLite remains the sole
installation-local persistent authority, and ISIN remains the durable cash
instrument identity.  Browser storage, request provenance, and legacy JSON do
not become parallel persistence authorities.

The server-owned composition adapter binds the exact watchlist ID, version,
revision hash, selected entry IDs, selected instrument IDs, temporary targets,
dedupe decisions, generated request ID, and canonical request hash.  Persistent
entries precede temporary targets; a persistent target wins an ISIN collision.
Temporary targets remain nonpersistent unless the user separately completes an
M8R-09 mutation preview and commit.

The adapter emits the existing Unified Market Evidence Request v1.  The request
continues through Mode A validation, Mode B1 preview, Mode B2 authorization,
one explicit Execute Once boundary, Mode C Result/Audit, and AI handoff.
Selection provenance is schema-validated, hash-bound into the control package,
verified before source dispatch, and projected as bounded identity metadata in
Result/Audit/Handoff.  Historical requests without this sidecar remain valid.

The UI exposes simple watchlist/request composition as the primary flow and
retains raw JSON as Advanced mode.  Watchlist mutation confirmation, evidence
authorization, and network Execute Once confirmation are separate.  The
500-entry storage bound remains distinct from the capability-catalog target
bounds (default 10, hard 50); no automatic batching, retry, polling, refresh,
or background execution was introduced.  Unified MCP remains exactly six tools.

## Acceptance evidence

The primary focused profile completed with `229 passed`.  An exact-code clean
clone completed with `228 passed, 1 skipped`; the one skip was environment
sensitive.  Contract/schema checks, both Skill validators, portable-catalog
sync, runtime/Skill/Guide semantic-drift validation, environment verification,
Python compilation, and JavaScript syntax checks passed.

A true `git clone --no-local` of the exact code commit completed the fresh
installation acceptance.  The deterministic E2E journey covered an initially
empty watchlist store, create/add preview and commit, process-style store reopen,
selection composition, Mode A, real B1/B2 control-package construction,
deterministic execute-once, and Mode C Result/Audit/Handoff.  It performed one
source invocation and no external market network operation.

Browser acceptance exercised the real `/workbench/` surface.  It found and
removed CSP-incompatible inline style use, then verified the page with no CSP
violation.  A hostile `<img src=x onerror=alert(1)>` target was rendered as inert
text through safe DOM APIs; no script executed.  No CDN, telemetry, remote font,
or browser durable-storage authority was added.

Default CI was executed in separate clean baseline and implementation clones.
Baseline: `2351 passed, 69 failed, 18 skipped`.  Implementation: `2373 passed,
69 failed, 18 skipped`.  The exact 69-node failure sets are identical, so new
failure nodes are empty and the failures remain
`INHERITED_NON_BLOCKING_DEBT`.

## Network and production state

No real live E2E was authorized or attempted.  Its classification is
`NOT_EXECUTED_POLICY_BOUND`; target, need, and source are null.  No market
network was used and no production watchlist or Security Master state was
mutated.

## Transition

Phase F is feature-complete for the planned v1 boundary.  Formal v1 release
readiness and contract freeze are the next authorized work; v1 release and
Phase G have not started.
