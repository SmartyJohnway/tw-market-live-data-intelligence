# V1 public error policy

Public Local Service and Unified MCP errors use stable machine-readable reason
codes. Clients must branch on the code, not an exception string, HTTP body
shape, filesystem path, or implementation class name.

## Initialization and identity

`SECURITY_MASTER_NOT_INITIALIZED` means this installation has no activated
local Security Master release. It is an expected fresh-install state and does
not permit a fixture fallback, automatic acquisition, or a raw filesystem
error to escape as a product response.

Identity validation returns its governed ambiguous, unsupported, or not-found
reason code. A known identity may remain resolvable while its requested
capability is non-executable; that is not a request to substitute data.

## Authorization and execution

`execution_confirmation_required`,
`network_execution_confirmation_required`, and
`market_fetch_requires_execute_mode` fail before authorization consumption,
source dispatch, or network access. A source failure is represented distinctly
from an unsupported/provisional capability boundary.

## Persistent Watchlists

Commands and previews are schema-validated. A caller must submit the exact
single-use preview id and content hash. `WATCHLIST_CONFIRMATION_MISMATCH` and
`WATCHLIST_PREVIEW_INTEGRITY_FAILED` make no mutation. Stale previews, expiry,
and optimistic version conflicts likewise fail closed.

The system does not expose raw prompts, full conversations, secrets, raw
legacy payloads, or market observations through watchlist mutation errors.
