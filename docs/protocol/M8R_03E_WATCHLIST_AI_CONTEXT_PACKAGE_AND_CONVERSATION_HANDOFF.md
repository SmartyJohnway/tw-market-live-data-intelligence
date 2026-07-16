# M8R-03E Watchlist AI Context Package and Conversation Handoff

## Purpose

M8R-03E projects accepted M8R-03C watchlist bundles, M8R-03D execution plans/results, and M8R-03D-F1 identity references into deterministic, read-only artifacts for a future AI conversation layer. It does not call an LLM, generate investment commentary, mutate watchlists, execute network sources, or create trading signals.

## Upstream dependencies

- M8R-03C owns validated evidence requests and snapshot/performance bundle semantics.
- M8R-03D owns preflight, source execution status, normalized observations, authorization boundaries, and source group results.
- M8R-03D-F1 owns governed identity, classification, lifecycle, snapshot IDs, record IDs, and record hashes.

The AI context package is a derived projection and is not a second source of truth.

## Producer-consumer architecture

```text
validated watchlist request
+ execution plan/result
+ snapshot/performance bundle
+ F1 identity references
→ watchlist_ai_context.json
→ watchlist_conversation_handoff.json
→ watchlist_ai_context_manifest.json
→ watchlist_ai_context_preview.md
```

The CLI accepts local JSON files only and writes deterministic local artifacts.

## AI-safe fact model

The package retains bounded identity summaries, lifecycle summaries, current observations, completed EOD references, and upstream performance metrics. It preserves source timestamp, retrieval timestamp, package generation timestamp, and official EOD trade date as distinct fields.

Forbidden interpretations include inferring active lifecycle from absence of evidence, treating retrieval time as market time, presenting EOD close as a current price, converting missing evidence to zero, or presenting unadjusted returns as adjusted/total returns.

## Citation model

Every material exposed identity, market, EOD, and performance value receives a `m8r_watchlist_ai_fact_citation.v1` entry with a deterministic citation ID, JSON Pointer fact path, source artifact type/ID/path, value hash, evidence status, and caveats. Validators reject duplicate citation IDs, unresolved fact paths, mismatched value hashes, orphan target citations, and unsupported statuses.

## Coverage model

Coverage is tracked at target and package level. Package statuses are controlled: `complete`, `partial`, `failed`, and `blocked`. Complete coverage requires every requested target to remain represented and have usable bundle coverage; partial/failure/blocking states are preserved rather than hidden.

## Missing-evidence model

Missing evidence uses `m8r_watchlist_missing_evidence.v1` with structured category, reason code, source family, blocking flag, recoverability, detail, and related citation IDs. Upstream conditions such as identity failure, source execution failure, currentness unresolved, stale observation, insufficient history, and artifact write failure remain structured.

## Currentness semantics

M8R-03E consumes upstream currentness where available. Missing source timestamps become currentness unresolved. Stale upstream statuses remain stale. Retrieval timestamps never prove market currentness. Completed EOD data is labeled as completed EOD reference rather than stale intraday data.

## Caveats and prohibitions

The package propagates classification, lifecycle, fixture, staleness, currentness, partial coverage, unadjusted-price, source failure, manual snapshot, and live-validation caveats. Prohibitions are controlled entries scoped globally or per target.

## Conversation handoff

The handoff is prompt-neutral and model-neutral. It lists answerable, partially answerable, and unsupported question categories, required disclosures, follow-up evidence options, response constraints, and citation requirements. Unsupported categories include causality, future prediction, buy/sell advice, dividend-adjusted return, news, and valuation when not evidenced.

## Context budgeting

Budgeting is deterministic and never removes requested targets. Identity and prohibitions are retained. If list limits are exceeded, omitted counts are recorded and a `context_truncated` caveat is added.

## Retention and security

Recursive validators reject forbidden fields such as raw payloads, raw HTML/cells, cookies, headers, authorization material, tokens, session IDs, MIS `msgArray`, browser frames, endpoint dumps, operator secrets, and one-shot nonces. The package may retain only bounded execution metadata such as execution mode, source group summaries, status, and network-calls-performed boolean.

## Failure-mode behavior

- Partial source failure: successful facts remain cited, failed source groups are disclosed, coverage is partial.
- All-source failure: identities may remain, market facts are not fabricated, retry requires new authorization where applicable.
- Blocked preflight: blocking issues remain, no source execution claim is made, and source facts are absent.
- Stale/unresolved currentness: caveats and missing evidence are added.
- Insufficient history: performance remains unavailable rather than zero.
- Artifact write failure: CLI returns structured failure and does not report a passed manifest.

## Fixtures

`tests/fixtures/m8r_03e/` contains complete snapshot, partial source failure, all-source failure, blocked target, stale/currentness unresolved, performance, fixture-only F1 evidence, and context-budget pressure cases.

## GO / GO_WITH_CAVEATS / NO_GO criteria

M8R-03E is GO_WITH_CAVEATS when schemas, builders, validators, fixtures, CLI, lineage, citations, coverage, failure states, and security scans pass while acknowledging no LLM invocation, no production conversation UI, no NLP target extraction, no persistent watchlist mutation, manual snapshot generation, and incomplete M8R-03D live validation.

NO_GO applies if uncited facts enter the package, partial coverage is labeled complete, retrieval time becomes market time, missing evidence becomes zero, unadjusted return is presented as total return, lifecycle is inferred without evidence, raw/auth material is retained, failed execution fabricates analysis facts, or target order/identity lineage is lost.

## Next task

Recommended next bounded task: `M8R-03F-CONVERSATIONAL-TARGET-INTAKE-AND-TEMPORARY-WATCHLIST-RESOLUTION`. Do not implement it in M8R-03E.
