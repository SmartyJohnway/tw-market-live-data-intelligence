# M5IJ explicit refresh end-to-end acceptance and local product release

Status: `m5ij_local_product_release_candidate` when non-network acceptance passes.

This review records the final local-first release hardening. M5F remains the canonical source for browser readonly preview, FastAPI readonly endpoints, MCP readonly tools, AI context pack, and ChatGPT briefing. M5I refresh is explicit, bounded, CLI-only, single-use authorized, and preserves last-known-good M5F promotion semantics. M5J hardening verifies docs, disabled legacy probe surfaces, no forbidden output fields, and no forbidden artifact paths.

Default commands do not make market-data network calls. Live refresh execution was not attempted in this release validation; user-environment authorization remains required.
