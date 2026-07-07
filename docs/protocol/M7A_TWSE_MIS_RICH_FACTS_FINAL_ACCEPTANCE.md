# M7A TWSE MIS rich facts final acceptance

Status:
- pass_with_caveats

## Completed tasks

- M7A-00 field forensics / inventory
- M7A-01 manual bounded probe harness
- M7A-01B failed attempt evidence
- M7A-01D successful fallback-repaired probe evidence
- M7A-02 schema-only contract
- M7A-02A v0.2 evidence alignment
- M7A-03 runtime parser extension
- M7A-04 fixture expansion and parser tests
- M7A-05 downstream compatibility checks
- M7A-06 final acceptance / closure

## Merged PR references

- PR #90
- PR #92
- PR #93
- this PR

## Evidence summary

- M7A-01D successful bounded probe summary exists.
- Operator-provided 2330 regular session / closing auction / post-close evidence was used for candidate semantics.
- Operator-provided official MIS detail-item evidence was used for UI cross-checking.
- Operator-provided t00 index evidence was used for index candidate fields.
- Mobile broker app evidence is supporting only.
- No official public TWSE MIS API field dictionary found.

## Runtime behavior

- TWSE_MIS normalized observations now include `twse_mis_rich_facts`.
- Top-level `z/y` fallback preserved.
- `reference_only` preserved.
- `pz` does not override top-level last price.
- `ps` does not override top-level current volume.
- Non-TWSE_MIS sources unchanged.

## Rich facts status

- runtime_populated=true
- parser_populated=true
- runtime_parsed_candidate
- safe_for_ai_context=false
- official_documented=false
- unit_verified=false
- api_field_dictionary_available=false

## Compatibility

- FastAPI checked.
- MCP checked.
- Frontend/watchlist rows checked.
- Conversation handoff / AI context checked.
- Source-health checked.
- Source capabilities checked.
- Latest observation read/write compatibility checked.
- Non-TWSE_MIS checked.

## Caveats

- No official API field dictionary.
- No realtime SLA.
- Quantity units remain market-mode-required.
- Displayed depth is only displayed depth snapshot.
- Not full order book.
- Not support/resistance.
- Not true liquidity.
- Not trading signal.
- AI exposure remains not safe by default.
- Odd-lot semantics not runtime-integrated unless future source mode evidence is added.

## Forbidden interpretations

These strings are recorded as forbidden interpretations, not as endorsed meanings:

- buy signal
- sell signal
- hold
- target price
- support/resistance
- main force
- true liquidity
- order-book truth
- realtime guarantee
- execution feed

## No-go confirmations

- No live probe in M7A-05/M7A-06.
- No new probe output committed.
- No cookies/headers/session tokens committed.
- No frontend/MCP/FastAPI behavior promotion unless compatibility tests require non-semantic tolerance changes.

## Acceptance decision

M7A is accepted as `pass_with_caveats`. The rich facts are runtime-populated candidate facts, not official TWSE MIS API field definitions. They remain unsafe for default AI context exposure and are not promoted into frontend, FastAPI, MCP, source-health, or source-capability semantics beyond generic observation payload tolerance.

## Next recommended track

- M7B or M7B-00: AI-safe market context projection / policy-gated exposure design.
- Or M7A-FOLLOWUP: official-source monitoring and session-mode/odd-lot evidence expansion.

Recommended next track: `M7B-AI-SAFE-MARKET-CONTEXT-PROJECTION-DESIGN`.
