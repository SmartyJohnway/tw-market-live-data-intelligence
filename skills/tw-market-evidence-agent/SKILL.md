---
name: tw-market-evidence-agent
description: Use this Skill when an agent must choose governed Taiwan market evidence capabilities and compose Unified Request JSON inputs.
---

# Taiwan Market Evidence Agent Skill

Use this Skill when you must query Taiwan market data, resolve security targets, check session states, or analyze historical end-of-day/intraday observation evidence.

---

## 1. Skill Trigger

This Skill applies whenever a user query specifically requires:
- **Current, official, verifiable, time-sensitive, calculated, or source-grounded** Taiwan market evidence (TWSE, TPEx, TAIFEX).
- Formulating a structured query to fetch canonical evidence.
- Determining whether the market is open, closed, or affected by disaster closures.

Do not use this Skill for:
- General finance theory or educational concepts.
- Non-Taiwan security inquiries.
- Pure textual formatting or analysis of already-provided historical context (where no new data refresh is needed).
- Simple Taiwan stock queries that only ask for general opinions or basic non-volatile information.

---

## 2. Mandatory Workflow

When triggered, the AI must follow this step-by-step workflow:

1. **Extract Intent & Targets**: Identify security codes, names, hints (TWSE/TPEx/TAIFEX), and desired metrics (EOD vs. current live-ish data).
2. **Resolve Ambiguity**: If ticker symbols are ambiguous or missing, stop and clarify with the user. Do not make assumptions or guess targets.
3. **Check Catalog Capabilities**: Consult the portable catalog projection (`assets/unified_capability_catalog_portable.json` or `references/capability_quick_guide.md`) to verify if the requested target-market combination is supported.
4. **Compose Unified Request**: Generate a request JSON matching `unified_market_evidence_request.v1.schema.json`. Set `execution_mode` to `"preview"`.
5. **F3 Validation and Handoff**: Pass the JSON request to the F3 deterministic validation layer (or ask the operator to do so). If F3 returns `requires_clarification`, ask the user for clarity. If `invalid` or `unsupported`, explain the limits. If `valid`, present the validated JSON request to the user and instruct them to execute it via their local workbench. **Direct Unified execution/MCP tools are not currently available to the AI.**
6. **Interpret Result**: Once the user pastes back the `unified_market_evidence_result.v1` payload (from 05B execution), parse it. Strictly preserve timing semantics (EOD vs. live-ish, stale vs. current).
7. **Respond with Traceability**: Summarize findings, present calculations clearly, and preserve trace links to citations.

---

## 3. Request Composition Rules

- **Schema Strictness**: All request objects must validate against the request schema. Do not inject ad-hoc parameters or obsolete Phase B operation names.
- **Data Needs Selection**: Use only the 7 official capability IDs. Avoid minimal sufficient limiting rules; retrieve all needs requested by the user within the authorized target scope.
- **Security Gating**: Do not attempt to bypass execution approvals. Never request or expose raw transport payloads, credentials, or session cookies.
- **Operator Execution**: Always rely on the operator to perform Mode A (Validate), Mode B (Preview/Execute), and Mode C (Package) via the manual workbench. Mode A/B/C are target manual operator workflows, not Unified JSON parameters.

---

## 4. Result Interpretation and Safety Rules

- **Facts First**: Base all conclusions on the returned Level 1 (durable governed evidence) and Level 2 (request-scoped time-sensitive evidence) canonical observations. Do not fabricate missing data.
- **Session Awareness**: Label EOD settlement as completed session statistics. Never present EOD data as real-time intraday quotes.
- **Staleness and Gaps**: If data is `stale` or target coverage is `not_found`, explicitly declare it. Do not fabricate or estimate missing data.
- **Safety boundaries and recommendation policy separation**:
  - The project output will never generate trading recommendations (buy/sell/hold/signals).
  - Conversational recommendations and analysis are permitted under AI conversational policy, provided that all evidence, caveats, time horizons, and uncertainties are clearly disclosed.

---

## 5. References

- `references/capability_quick_guide.md`
- `references/evidence_semantics.md`
- `references/tool_selection_examples.md`
- `references/current_limitations.md`
- `assets/unified_capability_catalog_portable.json`
