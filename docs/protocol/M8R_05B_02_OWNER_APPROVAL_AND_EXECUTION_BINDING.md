# M8R-05B-02 owner approval and execution binding

This offline contract binds an explicit owner decision to the exact immutable 05B-01 plan. Canonical UTF-8 JSON (`ensure_ascii=false`, sorted keys, compact separators, SHA-256) derives `umea-v1-` identities. Approval scopes are whole executable plan, selected operations, or selected batches; executable approvals are bounded to 24 hours and require single use, one maximum use, and `deny_replay`.

This task defines authorization only. It does not execute, retrieve evidence, or consume authorization. M8R-05B-03 owns atomic consumption and execution sequencing.

## Consumption binding
`unified_market_evidence_authorization_consumption_binding.v1` deterministically binds authorization, plan, scope, and replay controls. Supplied consumption state is only evaluated: missing, ambiguous, or consumed state fails closed. M8R-05B-02 does not write, lock, increment, or otherwise consume it.

## Acceptance and handoff
M8R-05B-02 is accepted with caveats; acceptance evidence is [M8R_05B_02_FINAL_ACCEPTANCE.json](../acceptance/M8R_05B_02_FINAL_ACCEPTANCE.json). The next task is M8R-05B-03 controlled unified market-evidence orchestration, which alone may atomically consume an authorization and invoke approved executors.
