# Phase H Official Source and Automation Authority Matrix

Status: **FROZEN**  
Freeze date: 2026-09-21  
Scope: H1 and H2 only  
Phase G baseline: `aa315918e0b5b431f4e63334c3ff91eac4e4e8f5`  
Owner review: `H0-01A ACCEPTED_WITH_MINOR_AMENDMENT`

The machine-readable normative authority is `Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.json`.

## 1. Normative source lanes

### Lane A — default candidate

Official OpenAPI, Government Open Data and ODGL-bound machine resources SHOULD be the default source lane after their route-specific activation gates pass.

`default_candidate` does not mean `active`.

### Lane B — official human verification

Official query pages, browser CSV exports, calculators and historical query pages MAY be retained as `manual_verification`. Their machine-readable output MUST NOT be treated as an unattended production API without an explicit automation authority.

### Lane C — optional licensed official provider

Official commercial products MAY be `optional_licensed_provider`. Account, payment, product license, delivery and redistribution terms MUST be satisfied before activation. Lack of subscription MUST NOT make the default portable installation invalid.

## 2. Source role and activation state

The following dimensions are independent:

```text
source_role:
  default_candidate
  governed_fallback
  optional_licensed_provider
  manual_verification
  research_only
  source_gap

activation_state:
  inactive
  eligible
  active
  blocked
```

`eligible` means source authority evidence is sufficient for later implementation consideration. It does not mean the route is registered, executable or production active.

This freeze sets **zero sources to `active`**.

## 3. Critical authority rules

The following rules are normative:

```text
official != free
machine-readable != automation-authorized
browser-downloadable CSV != production API
historical records exist != bounded historical retrieval supported
contract-supported subtype != runtime-executable route
eligible != active
```

No source MAY move to `active` without a separately authorized implementation and acceptance decision.

## 4. Historical retrieval semantics

Every source record MUST separate:

- `historical_records_exist`;
- `bounded_historical_retrieval_supported`;
- `historical_depth_if_known`;
- `retrieval_contract_status`.

For example, TWT49U records exist from 2020-03-02, but the current evidence does not prove that a runtime may issue an arbitrary target/date-bounded query. Its bounded retrieval flag therefore remains false.

## 5. Coverage and missing semantics

Source coverage MUST distinguish:

- complete;
- partial;
- unknown;
- source failed;
- binding failed;
- unsupported subtypes;
- not applicable.

No row MUST NOT be interpreted as no event unless the complete declared governed scope was successfully retrieved, source-contract validated and searched using exact target identity.

## 6. Frozen H1 authority summary

| Source | Role | Activation | License gate |
|---|---|---|---|
| TWSE attention | default candidate | inactive | H0-SRC-01A open |
| TWSE disposition | default candidate | inactive | H0-SRC-01B open |
| TWSE suspend/resume | default candidate | inactive | H0-SRC-01C open |
| TWSE changed trading | default candidate | eligible | dataset 11760 closed |
| TPEx attention | default candidate | eligible | dataset 11395 closed |
| TPEx disposition | default candidate | eligible | dataset 11396 closed |
| TPEx current suspend/resume | default candidate | inactive | H0-SRC-01E open |
| TPEx suspend/resume history | governed fallback | eligible | dataset 48665 closed |
| TPEx changed/periodic/managed | default candidate | eligible | dataset 11736 closed |

Lifecycle and complete-coverage claims remain subject to H0-SRC-02 even when the license authority is closed.

## 7. Frozen H2 authority summary

| Source | Stage | Role | Activation |
|---|---|---|---|
| TWSE TWT48U_ALL | preannouncement | default candidate | eligible |
| TWSE TWT49U | final official reference | optional licensed provider | inactive |
| TPEx `tpex_exright_prepost` | preannouncement | default candidate | eligible; dataset 11634 |
| TPEx `tpex_exright_daily` | final official reference | default candidate | eligible; dataset 11633 |
| TWSE capital reduction page/CSV | final reference | manual verification | inactive |
| TPEx capital reduction page/CSV | final reference | manual verification | inactive |
| TWSE par-value/split/consolidation | unresolved | source gap | blocked |
| TPEx par-value/split/consolidation | unresolved | source gap | blocked |

Preannouncement and final calculation MUST remain separate event stages.

## 8. Provider and market asymmetry

TWSE and TPEx MAY use different providers and transports. Normalization MAY align meaning, timing, coverage, missing semantics and citation shape. It MUST preserve authority, transport, license, native evidence and lifecycle differences.

## 9. Open and closed issue lineage

H0-SRC-01 is `superseded`, not deleted. It is decomposed into H0-SRC-01A through H0-SRC-01G.

Closed in this freeze:

- H0-SRC-01D: TWSE changed trading, dataset 11760;
- H0-SRC-01F: TPEx suspend/resume history, dataset 48665;
- H0-SRC-01G: TPEx changed status, dataset 11736;
- H0-SRC-13: TPEx ex-right/dividend preannouncement, dataset 11634.

Remaining issues are activation, provider, lifecycle or coverage gates. `contract_freeze=false` for every issue.

## 10. H3 boundary

H3 source findings remain H0-01A research input. This document does not freeze H3 capability semantics, select an H3 provider, or authorize H3 execution. H0-E remains DEFERRED.

## 11. Runtime boundary

This matrix does not activate any source, adapter, registry, route, Local Service, MCP, Workbench or preferred contract version. Exactly six MCP tools remain the governing surface.

No scheduler, polling, background refresh, automatic backfill, warehouse or scraper is authorized.

## 12. Provenance

Research inputs:

- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Official_Source_Transport_Automation_Authority_Matrix.md`
- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Source_Authority_Matrix.json`

Accepted pre-amendment hashes:

- Markdown: `566a91f5c7fa1da18dfb85753a19ba6f446973a5dc8040a3ac7996dde0fe31d3`
- JSON: `6a05968b4e2c6bd444bd90942eaffd9f24a55c99b17bd29365211ea3c5cd53f7`

Post-amendment SHA-256 values:

- Markdown: `120cd0278484b429cf618e9041b2bd0eb56edb0e43cee17d00be0af03347b7ef`
- JSON: `6685c236274b662107c0061240f6983e63ce68dee6daa33c1c3e2deef1ef7670`

Frozen artifact hashes are recorded in `PHASE_H_H0_A_D_FREEZE_MANIFEST.json`.
