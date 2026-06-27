# Authorization Index

M4 Omega governed platform skeleton index.

## M5A bounded controlled live probe authorization preflight

- [M5A live probe authorization request schema](live_probe_authorization_request_schema.json)
- [M5A live probe authorization package](LIVE_PROBE_AUTHORIZATION_PACKAGE.md)
- [M5A source candidate decision matrix](M5A_SOURCE_CANDIDATE_DECISION_MATRIX.md)

M5A is preflight-only. It keeps `live_probe_authorized=false`, `authorization_token_issued=false`, and `execution_performed=false` until a separate user authorization review.

## M5B bounded TWSE OpenAPI execution

- Execution authorization schema: `docs/authorization/m5b_live_probe_execution_authorization_schema.json`
- Decision: `docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json`
- Operator runbook: `docs/authorization/M5B_OPERATOR_RUNBOOK.md`
