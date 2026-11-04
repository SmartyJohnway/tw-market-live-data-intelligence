# Post-v1.5 v1.5.1 RMA-8 — Result / Audit / Evidence Integrity

Date: 2026-11-02
Disposition: **PASS / CLOSED**
Next boundary: **RMA-9 — Failure and recovery matrix — NEXT_UNDECIDED / NOT_STARTED**

## 1. Scope and authority

RMA-8 proves that successful user-visible Result V3 outputs are traceable back to governed execution evidence rather than to chat text or self-reported integrity flags alone.

Acceptance follows the RMA Test Contract: Control Package / authorization binding, execution receipt, evidence artifact existence and hash, citation binding, Result V3 reference, Audit Package reference and end-to-end lineage consistency.

No commit, push, tag, release, VERSION mutation, Stable repoint, Secure MCP Tunnel mutation or evidence deletion is authorized by this closure.

## 2. Candidate and environment

Diagnostic candidate SHA-256:
`F4B8049B4614C0ED2C4F0799315F0810CC2AE029CEA39FE2F857A8131881D333`.

The candidate remains **NONCANONICAL / NOT RELEASE-ELIGIBLE**. It contains the previously accepted D006, D007, D013 and D001 bounded repairs.

Fresh acceptance evidence:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-8\8B-fresh-lineage\attempt-02\`.
## 3. Fresh successful executions

Attempt-02 produced two successful executions used as the RMA-8 acceptance set:

- `monthly_revenue` for `TWSE:2330` — `full_success`, one governed evidence artifact and one citation;
- `trading_status_context` for `TPEX:5227` — `full_success`, seven governed evidence artifacts and seven Audit citation mappings.

`current_observation` also executed but returned a failed Result in this run. It is preserved as non-success evidence and is not represented as a successful RMA-8 lineage proof.

For every successful case the reviewer independently verified:

- persisted request, plan, authorization, control manifest, claim, receipt, evidence bundle, Result V3 and Audit Package exist;
- request hash binds to the plan and authorization binds the exact plan id/hash;
- the API-returned control-package manifest hash equals the guest-side SHA-256 of `control/manifest.json`;
- receipt, bundle, Result and Audit hashes independently recompute to their declared hashes;
- claim -> receipt and bundle -> receipt identities/hashes close;
- Audit -> authorization/plan/receipt/bundle/Result and replay-manifest references close;
- API Result/Audit/Handoff content equals the persisted governed artifacts.
Artifact-level verification was reviewer-owned rather than trusting the product's self-reported integrity flags:

- every Audit/Bundle inventory entry resolved to a real durable evidence file;
- every listed artifact matched its recorded raw SHA-256 and byte count;
- the evidence directory contained no unlisted JSON evidence artifacts;
- Audit citations mapped to real artifact path/hash pairs and governed operation ids;
- Result citations mapped back to the same Audit citation records and evidence hashes.

Machine posthoc adjudication:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-8\8B-fresh-lineage\attempt-02\POSTHOC_REVIEWER_ADJUDICATION.json`.

Final machine closure:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-8\RMA8_CLOSURE_ADJUDICATION.json`.

## 4. Harness adjudication

RMA-D016 is **CLOSED_PASS**. Attempt-01 failed before guest execution because a one-shot Windows Sandbox ID lookup raced environment enumeration. Attempt-02 used bounded unique-ID resolution and crossed the gate.

RMA-D017 is **CLOSED_PASS**. The attempt-02 reviewer incorrectly looked for the response-only `control_package_manifest_hash` inside persisted `authorization.json` and also required a non-success probe to satisfy success-lineage criteria. Preserved guest SHA evidence proves the successful cases bind the exact control manifest hash; all remaining reviewer checks were already PASS.
## 5. Final decision

RMA-8 is **PASS / CLOSED**.

The acceptance set contains two fresh successful executions with different evidence shapes: a single-artifact Phase-G path and a seven-artifact Phase-H composite path. Every successful execution in the acceptance set is traceable from user-visible Result V3 through Audit/receipt/bundle/authorization/plan/request to durable governed evidence bytes and hashes.

No chat output is treated as execution proof. Product self-reported integrity flags are corroborating evidence only; reviewer-owned hash and cross-reference verification is the acceptance authority.

No new product defect was found in RMA-8. RMA-D016 and RMA-D017 were harness-only and are CLOSED_PASS.

RMA-9 — Failure and recovery matrix remains **NEXT_UNDECIDED / NOT_STARTED** and is not authorized by this closure.
