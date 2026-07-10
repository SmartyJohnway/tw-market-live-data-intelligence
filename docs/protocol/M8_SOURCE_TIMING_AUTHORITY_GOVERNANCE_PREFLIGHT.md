# M8 Source Timing Authority Governance Preflight

- **Status**: `m8_00_governance_foundation_defined`
- **Track**: M8 source timing, authority, freshness, and AI exposure governance.
- **Next task**: `M8-00-04-SOURCE-FRESHNESS-EVALUATOR-PURE-HELPER`

## Scope

- M8-00 is source timing, authority, freshness, and AI exposure governance.
- M8-00 is not runtime source expansion.
- M8-00 is not a trading strategy layer.
- M8-00 is not a live polling layer.
- M8-00 does not make EOD data realtime.
- M8-00 does not promote manual evidence to official source.
- M8-00 does not promote validation-only source to primary source.

## 1. Purpose

M8-00 prepares official, reference, EOD, derivatives, regulatory, manual-evidence, validation-only, and credential-gated source governance for future M8A-M8G work. The purpose is to define how multi-source Taiwan market context must label timing, authority, freshness, delay, and AI exposure before any new source adapter or runtime integration is added.

The first goal is not more data. The first goal is to keep future source expansion safe, caveated, reproducible, and distinct from trading advice.

## 2. Accepted upstream

M8-00 accepts M7G final acceptance with status `final_acceptance_pass_with_caveats` as the upstream baseline. M7G established local safe context artifact load, controlled manual refresh execution, an explicit operator refresh gate, safe artifact validation and load gates, no raw payload exposure, and no trading advice.

Accepted M7G source route semantics:

- TWSE listed live = `TWSE_MIS` / `tse_{symbol}.tw`.
- TPEx/OTC live = `TWSE_MIS` / `otc_{symbol}.tw`.
- no TPEX_MIS.
- no rotc_.
- no emerging stock live route in M7G.

## 3. M8-00 covered tasks

- M8-00-00 Scope / Readiness / Source Governance Preflight.
- M8-00-01 Source Capability Registry v1.
- M8-00-02 Freshness / Timestamp / Delay Semantics Contract.
- M8-00-03 Multi-source Market Context Schema.

## 4. M8-00 not covered in this PR

- M8-00-04 Source Freshness Evaluator.
- M8-00-05 Multi-source Context Builder.
- M8-00-06 Controlled Conversation Context Integration.
- M8-00-07 Compatibility Hardening.
- M8-00-08 Final Acceptance.
- M8A official TWSE/TPEx EOD adapters.
- M8B TAIFEX official derivatives EOD/statistics.
- M8C attention/disposition.
- M8D corporate action/ex-right.
- M8E recent historical baseline.
- M8F derivatives + spot cross context.
- M8G M8 acceptance pack.

## 5. Allowed interpretation

Allowed wording examples:

- official EOD reference.
- bounded live-ish observation.
- manual operator snapshot.
- retrieved-at time is not necessarily exchange time.
- EOD-only source.
- not realtime guaranteed.
- validation-only supporting source.
- credential-gated provider research only.
- unavailable source.

## 6. Blocked interpretation

Blocked wording and semantics:

- buy / sell / hold.
- trading signal.
- target price.
- support / resistance.
- bullish / bearish recommendation.
- strongest / weakest ranking.
- leading indicator claim.
- EOD described as realtime.
- retrieve time described as exchange timestamp.
- manual evidence described as official API.
- validation-only source promoted to primary source.
- unofficial endpoint described as official documented API.

No trading advice may be generated from M8-00 governance artifacts.

## 7. Source family route principles

- TWSE_MIS is Level 2 bounded live-ish observation family.
- TWSE listed live route uses `tse_{symbol}.tw`.
- TPEx/OTC listed live route uses `otc_{symbol}.tw` through TWSE_MIS.
- There is no TPEX_MIS in M8-00.
- There is no rotc_ route in M8-00.
- TWSE_OPENAPI / TPEX_OPENAPI / TAIFEX_OPENAPI are official/reference/EOD or statistics families, not live refresh execution in this PR.
- TAIFEX_MIS is declared as live derivatives family, not executable in this PR.

## 8. Final result of this PR

Expected status: `m8_00_governance_foundation_defined`.

Expected next task: `M8-00-04-SOURCE-FRESHNESS-EVALUATOR-PURE-HELPER`.
