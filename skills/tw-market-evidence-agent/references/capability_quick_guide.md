# M8 AI Capability Quick Guide

Baseline SHA: `d6b83313bb301e652ae82b8583d73d2aaa1d753e`

Use this guide when an AI agent needs Taiwan market evidence without learning internal M8R task names.

## Choose the smallest sufficient capability set

| User need | Capability | Expect | Critical caveat |
|---|---|---|---|
| What can this repo provide? | `describe_market_capabilities` | Available evidence, limitations, unavailable areas | Contract-only in F1; no API yet. |
| Which security is meant? | `resolve_market_targets` | Code, venue, canonical identity, lifecycle, ambiguity | Do not invent identity. |
| Current price or live-ish observation | `get_current_market_evidence` | Bounded observation, retrieval time, source family, coverage | `retrieved_at` is not exchange event time; live-ish is not zero-latency realtime. |
| Official completed session OHLCV | `get_official_eod_reference` | Trade date OHLCV and official source provenance | Completed-session reference, not intraday current price. |
| 5/20-day movement | `get_price_performance_evidence` | Lookback, input lineage, unadjusted price return | Unadjusted return is not total return. |
| Derivatives context | `get_derivatives_market_context` | TAIFEX live-ish observations where implemented and official EOD settlement context | Do not claim roadmap enrichments are implemented. |
| Identity/lifecycle | `get_security_identity_and_lifecycle` | Canonical code, venue, name, state, execution policy | Missing lifecycle evidence is not confirmed active status. |
| Existing evidence package | `read_market_evidence_package` | Coverage, missing evidence, citations, lineage, currentness | Fixture validation is not live readiness. |
| Why/valuation/total return/regulatory reason | `identify_required_additional_evidence` | Supported vs unsupported claims and needed evidence | Do not hard-code refusal; explain what evidence is missing. |

## Evidence first, policy elsewhere

The repository supplies governed evidence, timing semantics, provenance, and deterministic calculations. The agent or product policy decides whether to provide opinions, scenarios, portfolio discussion, or recommendations. A recommendation should name evidence used, missing evidence, time horizon, and uncertainty.

## Raw payload boundary

Use normalized evidence by default. Raw payload exposure remains restricted unless an authorized audit workflow permits it. Never expose credentials, tokens, cookies, or secret-like fields.
