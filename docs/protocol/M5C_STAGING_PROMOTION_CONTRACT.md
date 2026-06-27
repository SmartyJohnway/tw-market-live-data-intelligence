# M5C Governed Staging Promotion Contract

M5C consumes the immutable M5B bounded evidence snapshot read-only. It does not replay live execution, consume new authorization, promote to staging/production, write generated artifacts, publish frontend files, or produce trading output.

## Binding
- Source run ID: `m5b_twse_openapi_20260627T015136Z`
- Source: `TWSE_OpenAPI` only.
- Exact targets: `2330`, `0050`, `00929`.
- Source manifest SHA-256 and staging candidate SHA-256 must match the committed M5B artifacts.
- Classification: `historical_evidence_snapshot`; freshness is EOD/historical and must not be displayed as current realtime.

## Required flags
- `dry_run_only=true`
- `actual_promotion_authorized=false`
- `production_write=false`
- `frontend_public_write=false`
- `generated_artifact_write=false`
- `trading_output=false`

Authorization request artifacts are request-only. Authorization decisions, approval tokens, and actual promotion commands are out of scope and forbidden in M5C.
