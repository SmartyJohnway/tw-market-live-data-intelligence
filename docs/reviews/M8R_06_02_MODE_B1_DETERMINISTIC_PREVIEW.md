# M8R-06-02 Mode B1 Deterministic Preview

Status: `PASS_WITH_CAVEATS`

Principal decision: `READY_FOR_M8R_06_03_AUTHORIZATION_REVIEW`. This is readiness only; M8R-06-03 and all later execution work remain unauthorized.

## Accepted vertical slice

The production path is now:

```text
Unified Request
→ production F3 with the governed compact Security Master
→ immutable 05B planning bindings
→ accepted M8R-05B-01 deterministic planner
→ internal orchestration plan
→ canonical Preview v1 projector
→ POST /api/unified/preview-request
→ Workbench Mode B1
```

The server reruns F3 for every Preview request and does not accept a client-supplied validation result. Planning binds canonical hashes for the original request, normalized request, complete F3 output, active compact index/manifest, capability catalog, planner, routing matrix, and handoff contract. The Preview remains separate from the internal orchestration plan. The feature implementation head is `d10e40545505e1abf17655ff51d1f607a6f808d8`; the final review correction head is `a16b0135abdacc1049229c2160733268493baaab`, which added meta-schema validation and explicit input/output error classification.

Every result explicitly preserves the boundary:

```text
PREVIEW ONLY
NO NETWORK EXECUTED
NOT AUTHORIZED
```

No authorization is created or consumed, no execution occurs, and no persistent runtime mutation or external source call is performed.

## Controlled compatibility corrections

Preview v1 received a `CONTROLLED_ADDITIVE_V1_COMPLETION`. Its version remains `unified_market_evidence_preview_response.v1`; previously valid payloads remain valid. The raw schema SHA-256 changed from `f05454cf4c085f8c991b1b57c4068d3780971048ea9fad87767b63c188923ff1` to `68592a194f71e519b6c2545e0a201342eccdfabf4b2fd9d9f07dc16fdf11e5d2`. All canonical F3 target statuses now have explicit Preview summary fields, and governed target failures map to `target_not_plannable` rather than capability or software errors. Ambiguity remains the distinct clarification state `ambiguous_target`.

The 05B planning boundary received a `CONTROLLED_05B_ROUTING_COMPATIBILITY_CORRECTION`: canonical `company_share/common_share` maps to the established routing class `equity` without mutating F3 identity. The planner and routing-matrix versions remain unchanged, and the routing matrix canonical hash remains `870c4d59f746bc29bf3c3f29c532767bab7df5107c21cc2a21c3e2f0865b710c`. ETF is not mapped to equity and remains fail-closed under the current route.

## Acceptance results

The executable scenario matrix covers TWSE current/EOD, TPEx current, optional partial coverage, required plan-only and blocked capabilities, all F3 target outcomes, duplicate targets, target and operation limits, TAIFEX provisional/unsupported planning, and malformed planning dependencies. A malformed Preview schema authority is meta-schema checked, maps to `input_schema_invalid`, and reaches the actual API as sanitized HTTP 409 `mode_b1_planning_dependency_unavailable`. A valid Preview schema that rejects generated output maps to `output_schema_invalid` and sanitized HTTP 500 `mode_b1_internal_error`.

An actual localhost subprocess served health and Workbench endpoints with HTTP 200. Real production Preview requests resolved `TWSE:2330` and `TPEX:5227` and returned `ready_for_confirmation`; the TWSE operation used routing security class `equity`. All network, authorization, and execution flags were false.

Validation recorded before the final evidence-only commit:

- Mode B1 focused unit tests: 31 passed.
- Workbench/API integration: 17 collected; the sealed-candidate test executed locally and passed.
- Preview contract: 15 passed.
- M8R-05B-01: 63 passed.
- Combined F3, Mode A, 05B-01, C1B, C2, Preview, and Workbench regression: 216 passed.
- Post-Commit-7 repository `default-ci`: 841 passed, 0 failed, 0 skipped, 0 deselected in 239.81 seconds. The exact streaming `python scripts/run_test_profile.py default-ci` command exited 0 on `a16b0135abdacc1049229c2160733268493baaab`.
- `compileall` and `git diff --check`: passed.

## Caveats

- The accepted compact candidate is Git-ignored/local-only. Its absence remains a fail-closed condition, never a fixture or network fallback.
- Playwright is not installed, so browser E2E is `NOT_RUN`; actual localhost server/API composition passed.
- GitHub remote CI is `NOT_RUN` at evidence generation and is not inferred from local CI.
- The existing Starlette/httpx TestClient deprecation warning remains.
- `tests/unit/test_m8r_05a_cross_contract_consistency.py` remains 6 passed / 3 failed due `PRE_EXISTING_CROSS_CONTRACT_FIXTURE_DRIFT`: the old `valid_result.json` lacks completed Result v1 fields such as `result_id`. It was not modified or misreported as passing.

There are no current M8R-06-02 blocking findings. M8R-06-03, M8R-06-04, M8R-06-05, M8R-07, and M8R-08/MCP remain `NOT_AUTHORIZED`.
