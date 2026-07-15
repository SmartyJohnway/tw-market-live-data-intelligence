# M8R-01F Canonical Request Hash and Semantic Duplicate Correction

Status: `m8r_01f_canonical_request_hash_and_semantic_duplicate_correction_go`

Decision: `GO`

Corrective gate: `M8R-01F-CANONICAL-REQUEST-HASH-AND-SEMANTIC-DUPLICATE-CORRECTION`

Completion state: `complete`

Recommended successor: `M8R-02-ONE-SHOT-MARKET-CONTEXT-EXECUTION-ORCHESTRATOR`

Next task state after this fix: `next_task=null`, `next_task_status=awaiting_operator_acceptance`

## Verified baseline

The local baseline was `4d4a6ac2d980ab8fa5b055cd6f0fdcff6bd63b60`, the merge commit for PR #135 / M8R-01. M8R-01 remains merged, but its status is now treated as `GO_WITH_REQUIRED_FOLLOW_UP_FIX` until this corrective gate is accepted.

## Corrected defect

M8R-01F corrects two identity defects before any M8R-02 execution work:

1. `normalized_request_hash` no longer hashes the complete normalized request object. It hashes a canonical semantic planning scope only.
2. Duplicate target comparison no longer compares raw `input_identity`. It compares canonical normalized execution semantics.

## Canonical identity model

| Identity | Field | Purpose | Hash-boundary rule |
|---|---|---|---|
| Request lifecycle identity | `request_id` | Trace one operator request lifecycle | Excluded from semantic request hash and plan hash. |
| Canonical semantic request identity | `normalized_request_hash` | Identify normalized semantic planning intent | Built from accepted executable targets, effective context/source scope, output policy, execution policy, and non-goal execution guards only. |
| Plan identity | `plan_id`, `plan_hash` | Identify the exact executable approved scope | Depends only on executable or execution-governing top-level plan fields. |
| Approval identity | `approval_id` | Identify one approval event bound to one exact plan hash | Approval timestamps and IDs are excluded from plan identity. |

## Rejected target treatment

Rejected targets remain visible in `normalized_request.rejected_targets` and `plan.rejected_targets` for audit and operator feedback. They do not enter `normalized_request_hash`, `plan_hash`, source mappings, or executable plan identity. Raw rejected target content, presentation metadata, and validation message text are therefore non-executable audit output only.

## Semantic duplicate treatment

Duplicate handling uses normalized execution semantics:

- aliases such as `equity`/`stock`, `future`/`futures`, `OTC`/`TPEX`, case differences, whitespace differences, display names, notes, and comments collapse deterministically when the executable semantics are identical;
- conflicts fail closed with `duplicate_target_conflict` when the same canonical target duplicate key has different effective contexts, exact target-level sources, derivative identity, session, mappings, or other target-scoped execution behavior;
- request-level source families remain an upper-bound allowlist, while target-level source families remain exact target selection.

## Effective request hash treatment

The semantic request hash uses effective target scope. It includes accepted target semantic scopes, effective target contexts, effective target sources, source-selection mode, execution policy, output policy, and non-goal execution guards. It does not separately include request-level context/source defaults after those defaults have already been resolved into target-level effective semantics. Unused request defaults therefore cannot change `normalized_request_hash` or `plan_hash`; defaults that actually change a target mapping still change both hashes through the target semantic scope.

## Derivative identity treatment

Options include normalized market, instrument type, symbol/product, underlying, expiry, strike, call/put, contract type, and session in the semantic scope. Call/put and contract type are case-normalized; strike is normalized through decimal formatting where possible; expiry is stripped and uppercased. Futures use Model A exact contract identity: `expiry`, `contract_type=monthly`, and `session=regular` are required and the target ID includes expiry and contract type, for example `TAIFEX:future:TX:202607:monthly`. A bare `TAIFEX` future such as `symbol=TX` without expiry is rejected as `ambiguous_identity`; `contract_selector=front_month` is explicitly rejected until a later selector contract defines dynamic approval and execution-receipt semantics. M8R-01F does not add weekly-option, after-hours, continuous-contract, front-month selector, or broader exchange contract identifier support.

## Non-scope

This corrective gate adds no network execution, source adapter invocation, one-shot orchestrator, API endpoint, MCP tool, frontend control, scheduler, polling, retry, cache/database, market-context product package, or M9 ingestion.

## Acceptance

M8R-01F is `GO` and complete because deterministic semantic request identity is established, lifecycle/presentation metadata is excluded from executable identity, semantic aliases collapse, true duplicate conflicts fail closed, rejected targets do not alter executable plan identity, executable-scope changes still alter plan hashes, and M8R-02 remains inactive pending separate operator acceptance.
