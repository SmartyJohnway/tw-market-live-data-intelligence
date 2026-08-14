# M8R-08D Local Operator Action Contract Realignment

## Decision

M8R-08D records the owner-approved Phase E product realignment. The supported product is self-hosted local operator use: local AI host → stdio MCP → loopback Local Service → governed sources. It is not a centrally hosted/public/remote/multi-tenant service. There is one LOCAL OPERATOR MCP product model, not Safe/Operator profiles.

Clear user retrieval intent in the active conversation is sufficient to initiate a future bounded one-shot market-evidence read. Notification or confirmation is UX/operator awareness, not security authorization. Ambiguity clarification remains task understanding, not a second permission ceremony.

## Existing authority reinterpretation

The current five-tool MCP is accepted historical M8R-08B/08C evidence and remains unchanged. Its documented inability to authorize/execute is true for the current runtime. Existing authorization artifacts are retained and reclassified for the future action path as internal governed execution tickets carrying plan/request binding, execute-once claim, replay denial, receipt, audit, and accounting—not a mandatory separate browser permission ceremony.

`market_fetch_evidence` is accepted as the single preferred future M8R-08E tool. It uses the canonical Unified Request and existing validation, planner, internal ticket, execution, Result, Audit, and handoff authorities. It is not implemented by this decision.

## Repository documentation audit

| Classification | Finding | Decision |
| --- | --- | --- |
| A historical evidence | M8R-08A blueprint; M8R-08B/08C reviews; statements that v1 has five safe tools/cannot execute | preserve unchanged |
| B current implementation | M8R-08B operator/protocol documents state five tools and no execution | retain factual current-runtime wording |
| C current pointer | `docs/INDEX.md` | add 08D successor decision and contract links |
| D future contract | M8R-08D protocol | define action, boundaries, ticket role, annotations, and 08E acceptance |

`docs/agent_usage_guide.md` and `README.md` contain older M8R-05A/M8-era limitation statements. They are historical/legacy orientation material rather than an authority for the current unified MCP runtime; this milestone does not rewrite them to claim unimplemented action behavior.

## Roadmap status

`ROADMAP_V3_1_FILE_NOT_PRESENT_IN_REPOSITORY`. The available post-M8C roadmap is not Roadmap V3.1, so M8R-08D does not invent or rewrite an authoritative V3.1 file. The successor contract freezes the intended Phase E sequence: E1 M8R-07 closed; E2 M8R-08 foundation closed; E3 M8R-08D contract realignment → M8R-08E one-shot execution → M8R-08F real agent closed-loop acceptance. Phase F persistent state follows stable conversation-local execute-once; Phase H owns recurring automation.

## Scope and validation

No runtime, server, schema, planner, Local Service, source, market network, or MCP tool change is made. `server/unified_mcp/` remains behaviorally unchanged and still exposes five tools only. This PR performs documentation/link validation and existing MCP regression closure only; automatic production market-network calls are zero.

## Next gate

Principal decision: `READY_FOR_M8R_08E_ONE_SHOT_MARKET_EVIDENCE_MCP_IMPLEMENTATION`.

M8R-08E remains **NOT_AUTHORIZED** until owner review and explicit authorization after this contract PR.
