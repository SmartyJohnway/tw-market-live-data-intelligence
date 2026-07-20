# Agent Usage Guide (M8R-05A-F2 Unified Version)

This guide instructs AI agents on when and how to utilize the Unified Market Evidence workbench. The AI acts as the **request author and evidence analyst**, generating structured requests and interpreting the resulting evidence.

---

## 1. Purpose

The Unified Market Evidence project provides a deterministic mechanism to resolve targets, query available market evidence, and check market currentness without relying on subjective natural-language interpretation. This guide ensures the AI understands the boundary between the project's data execution and the AI's own reasoning.

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
6. **Preview & Confirm**: Show the planned execution to the user and request explicit confirmation before executing.

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

## 8. Preview and Authorization Loop

To prevent unauthorized or abusive network actions, all executions must run through a preview-then-execute loop:
1. AI composes a request with `"execution_mode": "preview"`.
2. The project returns a Preview Response conforming to `unified_market_evidence_preview_response.v1.schema.json`.
3. AI displays the planned execution bounds (estimated network calls, target count, expected gaps) and the confirmation text to the user.
4. **The user must explicitly approve the action.**
5. Upon approval, AI submits the request with `"execution_mode": "execute"`.

---

## 9. Result Interpretation

When reading the `unified_market_evidence_result.v1` payload, the AI must strictly respect the returned semantics:
- **Timing taxonomy**: Do not describe an EOD reference as a "current live price".
- **Staleness**: If the result marks evidence as `stale` or `reference_only`, describe it in the past tense.
- **Coverage**: If a target resolution fails (`not_found`, `ambiguous`), explicitly report the failure instead of fabricating data.
- **Missing optional needs**: If optional needs are missing, explain what is missing and why.
- **Citations**: Preserve `citation_id`, retrieved timestamps, and artifact paths for auditability.

---

## 10. Complete Output Principle

The project operates under the principle of **Exhaustive output within the authorized request scope**. 
- The project will return all relevant records for the approved targets and needs.
- The AI must not prompt the project to filter or drop fields during execution.
- AI should summarize and explain the results for readability in the final chat response, but must retain trace links to the citations.

---

## 11. Follow-up Behavior

After presenting the result, AI can:
- Answer the user's analytical questions.
- Identify missing info and suggest a follow-up request.
- Ask for authorization to query optional needs if they were skipped.
- AI must not loop tools automatically without user interaction.

---

## 12. Manual Workbench Handoff

In environments without direct MCP/API tool execution, the AI operates via the Manual Workbench flow:
1. AI generates a valid Unified Request JSON.
2. AI instructs the operator to paste it into their local workbench interface.
3. The operator validates, previews, and executes the command.
4. The operator copies the resulting JSON or Markdown output and pastes it back into the AI conversation.
5. AI interprets the pasted evidence and answers.
