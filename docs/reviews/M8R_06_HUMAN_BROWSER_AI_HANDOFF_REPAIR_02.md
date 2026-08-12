# M8R-06 Human Browser AI Handoff Repair 02

## Status

`CODE_REPAIR_COMPLETE; PENDING_AFTER_MERGE_HUMAN_RETEST`

The accepted human package was never mutated. A temporary copy, with prior Mode C outputs omitted, was reprojected locally without a market request. It preserved TWSE EOD close `2395.00`, TPEX EOD close `34.45`, the TPEX classification-coverage-drift caveat, and excluded raw rich-facts dumps.

## Product corrections

- Mode C uses the M7B controlled standard projection for TWSE current observation and adds Mode-C-only Top-5 displayed-depth context with explicit caveats.
- Controlled current-observation admission is based on successful `TWSE_MIS` rich evidence, not the canonical target market, so verified TPEX targets receive the same governed projection and never a generic raw-rich-facts fallback.
- A blocked M7B promotion now fails closed before both Standard context and Top-5 context; no raw displayed-depth or parser internals are exposed.
- Raw parser/internal structures remain file-only evidence.
- Official EOD availability no longer depends on resolved calendar currentness; price and activity are admitted as optional v1 fields.
- Result v1 validates a meaningful official-EOD state (`status` or legacy `currentness_status`) and restricts enriched price/activity values to compatible scalar domains.
- Canonical operation identity is retained when legacy bounded classifier coverage drifts; the immutable source caveat remains in evidence lineage while AI-facing output reports the governed coverage-drift and verified-binding policy. True symbol/market mismatch fails closed.
- New output projector identity is `m8r_05c_v1_1`; legacy `m8r_05c_v1` packages remain exactly verified through frozen reconstruction.
- Markdown partial-failure numbering is one-based for display; canonical `target_index` remains zero-based.
- Workbench wording now makes explicit that network is only possible on Execute Once, and Mode C makes no additional market request.

## Boundaries

- external_market_network_calls: `0`
- human_browser_ai_handoff_retest: `PENDING_AFTER_MERGE`
- M8R-07: `NOT_AUTHORIZED`
- M8R-08: `NOT_AUTHORIZED`
