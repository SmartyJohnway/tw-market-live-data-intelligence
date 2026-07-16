# Taiwan Market Evidence Agent Skill

Use this Skill when an agent must choose governed Taiwan market evidence capabilities and preserve source, timing, lineage, caveat, and missing-evidence semantics.

## Required sequence

1. Understand the request: extract target(s), evidence type, time frame, current versus historical intent, authority requirement, comparison/calculation need.
2. Resolve ambiguity: identify ambiguous codes/names, unresolved venues, unclear historical/current intent, and total-return versus price-return ambiguity. Do not invent identity.
3. Select the smallest sufficient capability set from `references/capability_quick_guide.md`.
4. Inspect coverage and missing evidence: coverage status, source failures, currentness, lineage, calculation status, and fixture/live distinction.
5. Form the answer according to the user request and deployed AI policy. The Skill permits factual summaries, comparisons, interpretations, scenarios, opinions, recommendations, and risk/reward discussion when policy allows, with evidence and uncertainty disclosed; recommendations are not globally prohibited by this Skill.
6. Preserve evidence semantics: never transform settlement into current price, unadjusted return into total return, `retrieved_at` into exchange event time, partial coverage into complete coverage, fixture validation into live readiness, or missing lifecycle evidence into confirmed active status.

## References

- `references/capability_quick_guide.md`
- `references/evidence_semantics.md`
- `references/tool_selection_examples.md`
- `references/current_limitations.md`
- `assets/m8_ai_capability_contract.json`

## Security and raw data

Use normalized evidence by default. Do not request or expose raw payload unless a specific authorized audit workflow allows it. Do not expose credentials, tokens, cookies, session values, API keys, or secret-like fields.
