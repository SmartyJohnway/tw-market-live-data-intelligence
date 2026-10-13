# Phase K K2-B — Small Multi-Host Pilot & Compatibility Matrix

**Date:** 2026-10-13
**Status:** INITIAL THREE-HOST PILOT COMPLETE; Hermes and ChatGPT NATIVE_PASS; Antigravity CLI PARTIAL_HOST_LIMITATION / HOST_LIMITATION; host evaluation count 3

## Purpose

K2-B evaluates whether meaningfully different Agent hosts can use the same canonical TW-Market contract correctly. It follows the K0 rule **Validate interoperability, not behavioral conformity** and the K1 eight-scenario set.

K2-B does not compare investment advice quality, require identical reasoning, or require identical tool-call choreography. It does not add product capability, schema, MCP tools, source routes, or market acquisition.

## Authority chain

- K0 — Lean Compatibility Charter
- K1 — Minimal Common Conformance Scenario Set
- K2-A — Deterministic Evaluation Preparation
- K1-05 finalized stale supplement merged before this pilot

The K2-A preparation manifest must report `known_preparation_gaps=[]` before any host receives a compatibility outcome.

## Initial pilot hosts

The initial pilot uses three meaningfully different hosts:

1. **ChatGPT** — primary user host; cloud conversation using Secure MCP Tunnel to local TW-Market. The current project conversation remains evaluator; the ChatGPT test subject must use a fresh conversation.
2. **Hermes Agent** — independent multi-provider Agent host with native MCP. Local preflight observed Hermes Agent `0.21.5`; version is evidence metadata, not a product requirement.
3. **Antigravity CLI** — Google Agent CLI with native MCP. Local preflight observed `agy 1.3.3`; version is evidence metadata, not a product requirement.

Codex CLI is retained as an optional reference/fourth host, not required for the initial three-host claim. Antigravity Desktop, Antigravity IDE, and the VS Code extension are surfaces in the same ecosystem and are not counted as additional initial hosts.

## Shared deterministic kit

All three hosts must consume one preparation instance generated from the same merged repository commit with:

```text
python scripts/prepare_phase_k_k2_deterministic_eval.py --root <disposable-shared-root>
```

The shared instance contains finalized success, stale, and partial Result/Audit/Handoff packages plus the remaining K1 scenario assets. The root is supplied at invocation time and is not a product dependency or repository path requirement.

The same prepared instance is used across hosts for comparison. It must show:

- eight K1 scenario mappings;
- `known_preparation_gaps=[]`;
- exactly six canonical MCP tools;
- market/source GET/HEAD/POST = 0;
- no compatibility outcome already claimed.

## Scenario execution rules

Each host is evaluated against K1-01 through K1-08. Scenario intent and semantic expectations remain common, while host-native planning and read-only call order may vary.

K2-B MUST NOT require:

- identical reasoning traces;
- identical final prose;
- identical read-only tool order;
- universal Preview for a read-only task without a canonical precondition;
- a copied third-party runtime or exact executable hash;
- host-specific core semantics.

K2-B MUST preserve:

- correct six-tool discovery;
- identity fail-closed behavior;
- Preview/authorization separation where execution is involved;
- execute-once semantics;
- Result/Handoff lineage;
- stale/currentness truthfulness;
- partial/source-failure distinction;
- unsupported capability fail-closed behavior;
- no trading/recommendation claim in canonical evidence.

No fresh TWSE, TPEx, TAIFEX, MOPS, or other market/source request is permitted in this pilot.

## Observation and adjudication

For each host/scenario, record the K2-A observation fields:

```text
scenario_id
host_label
host_version_observed
transport
outcome
finding_class
observed_tools
semantic_summary
known_limitation
evidence_refs
```

Outcome and root cause remain separate. A host limitation, adapter gap, documentation gap, harness failure, or test-infrastructure failure must not be collapsed into `PRODUCT_COMPATIBILITY_DEFECT`.

Do not auto-score compatibility. The evaluator adjudicates observations against K0/K1 product invariants after seeing the host transcript/tool evidence.

If a host limitation can be addressed by documentation, packaging, profile configuration, or an adapter, prefer that over a core fork. If a genuine product defect is discovered, pause the affected scenario and repair the product once; do not create host-specific semantics.

## Pilot execution order

Recommended order:

1. Hermes — independent CLI/Agent path and clean MCP configuration;
2. Antigravity CLI — independent Google Agent CLI and clean MCP configuration;
3. ChatGPT — fresh test conversation through Secure MCP Tunnel, with this project conversation remaining evaluator.

The order is operational convenience only and is not a product requirement.

## Local preflight at K2-B entry

Observed on the current Windows installation:

- Hermes Agent `0.21.5`; native MCP available; no MCP servers configured at entry.
- Antigravity CLI `1.3.3` at the user-local `agy.exe`; native MCP available; no MCP servers configured at entry.
- ChatGPT local access is available through the existing Secure MCP Tunnel path; a fresh ChatGPT conversation is required when the ChatGPT test run begins.

These paths and versions are local pilot evidence only. They are not frozen product dependencies and are not required of other installations.

## Start state

K2-B is formally STARTED when this authority is committed from a main that contains the merged K2-A and finalized K1-05 preparation state.

At start:

```text
host evaluation count = 0
compatibility outcomes = none
market/source requests = 0
K2-A gaps = 0
Phase K checklist = unchecked
```

The next action is host transport/profile attachment and the first controlled K1 scenario run. Do not broaden the host list or add live market acquisition during the initial pilot.
