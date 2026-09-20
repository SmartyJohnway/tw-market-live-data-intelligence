# Phase H H2 Price-Basis Corporate Action Contract

Status: **FROZEN**  
Freeze date: 2026-09-21  
Capability: `corporate_action_context`  
Phase G baseline: `aa315918e0b5b431f4e63334c3ff91eac4e4e8f5`  
Owner review: `H0-01A ACCEPTED_WITH_MINOR_AMENDMENT`

## 1. Purpose and boundary

`corporate_action_context` means quote-relevant price-basis corporate-action evidence. H2 exists to answer whether an official event changes the price-comparison basis relevant to a current or recent quote.

H2 MUST NOT become a general corporate-action database. It MUST NOT provide full corporate history, all dividends, all MOPS events, all board resolutions, shareholder-meeting history, adjusted-price series or total-return history.

## 2. Frozen initial taxonomy

The initial conceptual event vocabulary is:

- `ex_dividend`;
- `ex_right`;
- `ex_right_dividend`;
- `capital_reduction_resume`;
- `par_value_change_resume`;
- `split`;
- `reverse_split`;
- `share_consolidation`;
- `cash_capital_increase_effect`, only when it directly participates in an official reference-price calculation;
- `other_official_reference_price_event`, only with explicit source proof.

Taxonomy presence does not imply that a runtime route exists. Unsupported subtypes MUST remain visible in coverage.

## 3. Applicability and binding

The initial scope is TWSE and TPEx `company_share/common_share` under the existing Security Master.

Source binding MUST use resolved market plus exact security code. Company name MUST NOT be used as fallback identity. Provider asymmetry is allowed and MUST remain explicit.

## 4. Event stages and lifecycle

Conceptual stages MAY include:

- `announced`;
- `scheduled`;
- `effective`;
- `official_reference_calculated`;
- `corrected`;
- `amended`;
- `cancelled`;
- `unresolved`.

`corrected`, `amended`, `cancelled`, `supersedes`, and same-event relationships MUST NOT be inferred from target, date, text similarity, source snapshot difference or locally computed record hashes. They require official source linkage. Without that linkage, revision relation MUST remain `unresolved`.

## 5. Preannouncement versus final calculation

The following distinctions are normative:

| Market | Preannouncement | Final official reference context |
|---|---|---|
| TWSE | `TWT48U_ALL` official OpenAPI/ODGL | `TWT49U` optional licensed provider |
| TPEx | `tpex_exright_prepost`, dataset 11634, official OpenAPI/ODGL | `tpex_exright_daily`, dataset 11633, official OpenAPI/ODGL |

A preannouncement MUST NOT be labeled or projected as a final official reference calculation. A final calculation MUST retain its own source contract, stage and timing.

## 6. Conceptual evidence model

H2 target evidence MUST be capable of representing:

- event type and event stage;
- announcement/report time and effective date;
- pre-event close when officially supplied;
- official reference price and opening-reference basis when supplied;
- cash dividend, stock-dividend ratio, rights ratio and subscription price when supplied;
- source family, source contract, transport, license and observed-at;
- revision relation with status, relation type and related official reference;
- coverage status, covered and uncovered subtypes, and failed source families;
- governed citation identifiers.

Exact V3 JSON Schema syntax is DEFERRED to H0-G.

## 7. Missing, zero and unknown

The following states are distinct and MUST remain distinct:

```text
blank
0
not announced
not applicable
unavailable
source failure
```

Missing cash dividend, stock dividend ratio, subscription ratio, subscription price or reference price MUST NOT be normalized to zero.

Source-native placeholders such as `尚未公告` MUST remain semantically different from numeric zero.

## 8. Capital reduction

`capital_reduction_resume` is contract-supported.

TWSE and TPEx official human query pages and machine-readable browser CSV exports exist. A documented unattended production API authority was not proven. Therefore both routes remain `manual_verification` and `inactive`.

No HTML/CSV scraping workaround is authorized.

## 9. Par value, split and consolidation

Official concept/formula authority exists, but a governed common-share event feed was not proven for either market.

`par_value_change_resume`, `split`, `reverse_split` and `share_consolidation` remain contract vocabulary with source role `source_gap` and activation state `blocked`.

H2 MUST NOT claim complete price-basis coverage while a relevant requested-window subtype is uncovered.

## 10. Coverage model

H2 coverage MUST be richer than a single boolean. It MUST be capable of expressing:

- `complete`;
- `partial`;
- `unsupported_subtypes`;
- `source_failed`;
- covered event subtypes;
- uncovered event subtypes;
- failed source families.

No row MUST NOT mean no event unless the complete governed source scope for all relevant subtypes and the requested window was successfully retrieved and validated.

Later H4 semantics MAY claim `no_material_discontinuity_detected` only when relevant H2 event coverage is sufficiently complete. H4 exact semantics remain DEFERRED to H0-F.

## 11. Provider asymmetry

TWSE and TPEx MAY use different official providers, transports, license lanes and lifecycle stages.

The product SHOULD normalize meaning, timing, coverage, missing states and citation linkage. It MUST NOT normalize away source authority, transport, license, lifecycle limitations or provider availability.

## 12. Optional licensed providers

`optional_licensed_provider` is a first-class source role. TWT49U is the initial example.

An optional provider MAY improve coverage. Lack of a subscription MUST produce provider unavailable, route inactive and partial/unsupported capability coverage. It MUST NOT make a portable public installation invalid unless later Owner policy explicitly changes that rule.

Historical records existing in a licensed product does not prove arbitrary bounded historical retrieval. `historical_records_exist` and `bounded_historical_retrieval_supported` MUST remain separate.

## 13. Execution and persistence

H2 acquisition MUST remain explicit, target-scoped, data-need-scoped, time-bounded, authorized, execute-once and auditable.

No scheduler, polling, background refresh, automatic backfill, corporate-action warehouse, adjusted-price database or full-market persistence is authorized.

## 14. Provenance and freeze boundary

Research inputs:

- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Official_Source_Transport_Automation_Authority_Matrix.md`
- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Source_Authority_Matrix.json`

Accepted pre-amendment SHA-256 values:

- Markdown: `566a91f5c7fa1da18dfb85753a19ba6f446973a5dc8040a3ac7996dde0fe31d3`
- JSON: `6a05968b4e2c6bd444bd90942eaffd9f24a55c99b17bd29365211ea3c5cd53f7`

Post-amendment SHA-256 values:

- Markdown: `120cd0278484b429cf618e9041b2bd0eb56edb0e43cee17d00be0af03347b7ef`
- JSON: `6685c236274b662107c0061240f6983e63ce68dee6daa33c1c3e2deef1ef7670`

This file's hash is recorded in `PHASE_H_H0_A_D_FREEZE_MANIFEST.json`.

This document freezes semantics only. It does not create V3 schema bytes, source adapters, routes or current runtime authority.
