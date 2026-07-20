# Agent Usage Guide (M8R-05A-F2 Unified Version)

This guide instructs AI agents on when and how to utilize the Unified Market Evidence workbench. The AI acts as the **request author and evidence analyst**, generating structured requests and interpreting the resulting evidence.

---

## 1. Purpose

The Unified Market Evidence project provides a deterministic mechanism to query available market evidence and check market currentness without relying on subjective natural-language interpretation. This guide ensures the AI understands the boundary between the project's data execution and the AI's own reasoning.

> [!WARNING]
> **Current Runtime Limitations**
> The project currently provides the schema, policies, and manual contract handoff structures. **Unified intake, direct preview orchestration, and automated Unified execution via MCP or F3 resolvers are NOT yet implemented.**
> The AI currently can only author schema-valid requests and perform manual handoff via the operator. Future phases (F3, 05B, 05C) will build the direct automated runtime. Do not claim the Unified executor is currently available to the AI.

---

## 2. When to Call the Project

AI agents should propose invoking the project when the conversation requires:
- **Taiwan Cash Market Status**: Current intraday or recent cash-market status (TWSE, TPEx).
- **Official Reference Data**: Official End-of-Day (EOD) metrics (OHLCV, trade volume) or derivatives statistics.
- **Security Verification**: Verifying the canonical identity, ticker symbol, market venue, or listing lifecycle state.
- **Currentness & Session Diagnostics**: Determining whether a specific date/time is an active trading session or a holiday.
- **Evidence Semantics**: Demanding official citations, retrieved timestamps, provenance hashes, or coverage audits.
- **Explicit Instruction**: When the user explicitly requests querying latest or official exchange data.

---

## 3. When NOT to Call

AI agents should **NOT** invoke the project for:
- **General Financial Concepts**: Definitions, educational materials, or standard economic theory.
- **No-refresh / Existing Context**: When sufficient historical evidence is already present in the conversation context and no refresh is requested.
- **Non-Taiwan Markets**: Queries regarding US, Japanese, or other global exchanges not supported by the capability catalog.
- **Pure Textual Formatting**: Editing, translating, or formatting previously retrieved data.

---

## 4. AI Decision Process

When processing a user query, the AI must follow this reasoning workflow:
1. **Understand Intent**: Analyze the conversation context and identify if market evidence is required.
2. **Determine Targets**: Identify ticker codes, security names, and target venues.
3. **Identify Data Needs**: Select from the 7 defined capability needs (e.g., `identity`, `current_observation`, `official_eod_reference`).
4. **Clarify Ambiguity**: If target symbols are ambiguous (e.g., "台積" vs "台積電"), **ask the user** for clarification instead of letting the project guess.
5. **Compose Unified Request**: Build a valid JSON request conforming to `unified_market_evidence_request.v1.schema.json`.
6. **Manual Handoff**: Provide the JSON to the user/operator to run manually in the workbench.

---

## 5. Unified Request Authoring

A Unified Request must be a JSON object with the following fields:

```json
{
  "schema_version": "unified_market_evidence_request.v1",
  "request_id": "unique-uuid-or-string",
  "targets": [
    {
      "input": "2330",
      "market_hint": "TWSE",
      "resolution_requirement": "exact"
    }
  ],
  "data_needs": [
    {
      "type": "official_eod_reference",
      "priority": "required"
    }
  ],
  "execution_mode": "preview"
}
```

### Request Fields:
- **`schema_version`** (string, required): Must be exactly `"unified_market_evidence_request.v1"`.
- **`request_id`** (string, required): A unique client-supplied tracking identifier.
- **`targets`** (array, required): Tickers or symbols to query.
  - `input`: The search string.
  - `market_hint`: Optional venue constraint (`"TWSE"`, `"TPEX"`, `"TAIFEX"`, or `null`).
  - `resolution_requirement`: Optional constraint (`"exact"`, `"allow_ambiguity"`, or `"best_effort"`).
- **`data_needs`** (array, required): Desired capabilities.
  - `type`: One of the 7 supported capability types.
  - `priority`: `"required"` or `"optional"`.
  - `parameters`: Only required for `recent_performance` (lookback days).
- **`execution_mode`** (string, required): `"preview"` or `"execute"`.

---

## 6. Target Authoring and Ambiguity

AI must prioritize canonical code identification. If multiple matches or ambiguous targets exist:
- Propose the candidate targets back to the user.
- Ask: *"Please confirm if you meant TWSE 2330 (TSMC) or TPEx 5347 (World Advanced)?"*
- Do not submit ambiguous inputs to the executor without setting `resolution_requirement` appropriately.

---

## 7. Data Needs Catalog

AI must only request capabilities listed in the canonical catalog:
1. **`identity`**: Canonical security registration and lifecycle details.
2. **`current_observation`**: Latest live-ish snapshot (not guaranteed zero-latency realtime).
3. **`official_eod_reference`**: Official completed-session EOD OHLCV data.
4. **`recent_performance`**: Historical movement calculations (requires parameter `lookback_trading_days`).
5. **`session_status`**: Market session status and emergency closure states.
6. **`source_currentness`**: Metadata regarding retrieval times and effective trade dates.
7. **`evidence_quality`**: Quality assertions, caveats, and gaps in the retrieved data.

---

## 8. Target Operator Workflows (Mode A, B, C)

While the AI composes the JSON request, the actual execution is performed by the human Operator or Frontend Workbench using specific workflows. **These Modes are NOT AI JSON request parameters.** They are the target manual processes the operator follows:

- **Mode A (Inspect and Validate)**: The operator reviews the AI's proposed target lists and data needs. The workbench validates the schema without making external network calls.
- **Mode B (Preview, Authorize, Execute Once)**: The operator runs a dry-run preview, views estimated network costs and target scopes, explicitly authorizes the action, and the workbench executes it.
- **Mode C (Package and Handoff)**: The workbench generates a bundled snapshot of canonical evidence and passes it back to the AI context.

> [!NOTE]
> The existing legacy workbench does not yet implement the full Unified Request/Preview/Result lifecycle. AI produces schema-valid requests for review and future intake. Mode A/B/C represent the target workflow after Workbench realignment.

---

## 9. Evidence Lifecycle (Level 1 and Level 2)

- **Level 1 (Durable Governed Evidence)**: Stable, long-term governed evidence. Examples include canonical security identity, accepted official EOD references, and stable registry evidence.
- **Level 2 (Request-Scoped Time-Sensitive Evidence)**: Transitory evidence tied to a specific request. Examples include one-shot live-ish observations and request-bound currentness.

> [!NOTE]
> A single Unified Result can contain both Level 1 and Level 2 data.
> "Raw transport payload" versus "canonical normalized evidence" is a completely separate dimension. Raw transport payload belongs to audit artifacts and is NOT equivalent to Level 1.

---

## 10. Result Interpretation

When reading the `unified_market_evidence_result.v1` payload (e.g., pasted by the operator via Mode C), the AI must strictly respect the returned semantics:
- **Timing taxonomy**: Do not describe an EOD reference as a "current live price".
- **Staleness**: If the result marks evidence as `stale` or `reference_only`, describe it in the past tense.
- **Coverage**: If a target resolution fails (`not_found`, `ambiguous`), explicitly report the failure instead of fabricating data.
- **Missing optional needs**: If optional needs are missing, explain what is missing and why.
- **Citations**: Preserve `citation_id`, retrieved timestamps, and artifact paths for auditability.

---

## 11. Complete Output Principle

The project operates under the principle of **Exhaustive output within the authorized request scope**. 
- The project will return all relevant records for the approved targets and needs.
- The AI must not prompt the project to filter or drop fields during execution.
- AI should summarize and explain the results for readability in the final chat response, but must retain trace links to the citations.

---

## 12. Manual Workbench Handoff

Because the Unified Orchestrator and direct MCP execution are **future F3 deliverables**, the AI must currently operate via Manual Workbench Handoff:
1. AI generates a valid Unified Request JSON.
2. AI instructs the operator to paste it into their local workbench interface (performing Mode A).
3. The operator validates, previews, and executes the command (Mode B).
4. The operator copies the resulting Level 2 Canonical JSON or Markdown output and pastes it back into the AI conversation (Mode C).
5. AI interprets the pasted evidence and answers.
