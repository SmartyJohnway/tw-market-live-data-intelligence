# J-B03-S3 — Native Evidence Fallback Product Contract

**Disposition:** `J_B03_S3_NATIVE_EVIDENCE_FALLBACK_ACCEPTED`

**Product classification:** `NATIVE_EVIDENCE_FALLBACK_SUFFICIENT_FOR_J_B03_CONVERSATIONAL_CORRECTNESS`

## Decision

The product contract accepts exact, governed TPEx source-native evidence with explicitly unresolved marker semantics as useful and conversationally safe. This follows the PR #303 relevance rule: a capability gap blocks J when its absence can materially mislead a human and cannot be handled safely with fail-closed behavior. The PR #303 record treats honest `unresolved`, `unsupported` and `missing` outcomes as valid acceptance results where they prevent a false conclusion.

This decision does **not** change S2D. Official marker authority remains unverified: `SuspensionOfTrading = \uff39` (U+FF39) cannot be normalized to `stopped=true` or canonical `status_type=suspension`. The accepted evidence may say that, for an exactly bound TPEx security and source date, dataset 11736's `停止交易` field contains the raw value `\uff39`, cite its source, and explain that the code meaning is unresolved.

## Conversational outcomes

| Scenario | Accepted behavior |
| --- | --- |
| Ask what the official field says | Report the exact field, raw value, target, date, source and citation. |
| Ask whether it is currently stopped | Report the raw official value and say the system cannot safely answer yes/no from it. |
| Ask whether it can trade normally | Do not infer normal/tradeable from the marker, a blank, or an absent row; answer unresolved/insufficient. |
| Ask the exact resumption time today | Return unsupported/unresolved when no governed source proves the time. S1B already classifies this detail as optional for representative J-B03. |
| Ask about historical suspension/resumption | A governed history item may report bounded recorded events; it does not prove current state, complete lifecycle, or event linkage. |

Wrong affirmative, wrong negative, and unsupported normal/tradeable claims remain unacceptable. An honest unresolved answer accompanied by exact official evidence is acceptable and more useful than returning only “unsupported”: it preserves what source, field, value, target and date were observed while identifying the unresolved semantic step.

## Handoff and runtime guards

Any future AI handoff must carry the source family/contract, TPEX market and exact security identity, source record date and observation time, native field and label, exact raw value, `semantic_status=unresolved` (or an existing equivalent), caveat, coverage limits, citation, provenance and audit lineage.

An AI **must not** translate `SuspensionOfTrading = \uff39` alone into “stopped,” “currently suspended,” “cannot trade,” or a Boolean affirmative. It may quote the official field and explain that its code meaning is unresolved. The runtime must not normalize the marker, synthesize an effective lifecycle, claim suspension/resumption, or infer normal trading from a blank or absent row.

The frozen H1 conceptual contract permits bounded source-native evidence and `status_lifecycle=unresolved`. The current `trading_status_context_evidence.v1` schema, however, nests source-native provenance under an item that also requires a canonical `status_type`. This record does not claim that the existing schema can carry a native-only item without mislabeling it. The next design gate must establish a safe existing representation first; if none exists, it must raise a narrowly scoped contract/schema decision before implementation.

## J-B03 scope

The marker-semantic gap is **non-blocking** under this fallback contract. J-B03 itself remains **HOLD** pending implementation and representative acceptance. The representative minimum is TPEx attention, TPEx disposition, and exact-target/date-bound `tpex_cmode` native evidence with unresolved semantics, citation and safe AI handoff. Bounded `tpex_spendi_history` evidence is optional support for historical-event questions; unsupported event timing and unselected coverage may fail closed. No full-H1 claim follows.

`H0-SRC-01E` remains OPEN; `tpex_spendi_today` source authority is unresolved but its precise current-event detail is not required for this representative conversation. `H0-SRC-02` remains OPEN for full-H1 lifecycle/completeness. Neither is closed here.

## State and boundary

- Recommended next gate: **J-B03-A2 — Deterministic Native-Evidence Adapter / Aggregation Design**, under separate Owner authorization.
- Market-data GET/HEAD/POST = **0**; no source acquisition occurred.
- No production code, schema, catalog, routing, registry, activation or MCP change; MCP remains 6.
- J-B03 = HOLD; J-B04 = BLOCKING; Phase J = NOT STARTED.
- `data/` and historical PR #309–#312 records were not modified.

The companion JSON contains the full scenario analysis, handoff/runtime guard contract, issue states and change-boundary record.
