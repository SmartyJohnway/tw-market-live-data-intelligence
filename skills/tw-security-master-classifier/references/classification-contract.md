# Classification Contract

## Contents

1. Output dimensions
2. Authority order
3. Deterministic rules
4. Confidence and quarantine
5. Current listed-common-stock flag

## 1. Output dimensions

Keep these dimensions separate:

```text
asset_class
instrument_family
instrument_type
equity_subtype
market
board
current_observation_status
listed_common_stock_core_flag
```

Examples:

- An ETF can trade on TWSE but is not company equity.
- A preferred share is equity but not a common share.
- An emerging common share is a common share but not TWSE/TPEx listed-common-stock core.
- A security present in a current ISIN snapshot is `observed_current`; that alone does not prove it is actively tradable.

## 2. Authority order

1. Official route and `strMode`.
2. Page and section heading.
3. Market or board field.
4. Controlled CFI mapping.
5. ISIN and remarks.
6. Code or name patterns only as warnings.

Section evidence overrides a generic page collection. A mixed page such as mode 2 or 4 cannot be classified from mode alone.

## 3. Deterministic rules

### Route-level families

| Mode | Default family | Rule |
|---:|---|---|
| 3 | debt security | May be refined by section and CFI |
| 6 | derivative | Refine to future or option from section/CFI |
| 7 | collective investment vehicle | Refine from fund section |
| 9 | gold spot | Do not classify as equity |
| 10 | negotiable certificate of deposit | Do not classify as equity |
| 11 | index | Do not classify as a tradable company security |
| 12 | security token | Use CFI to distinguish debt/equity-like token when supported |

Modes 1, 2, 4, 5, and 8 require section and/or controlled CFI evidence.

### Controlled CFI rules

Use only controlled mappings that the bundle tests. Expand mappings only with official CFI documentation or accepted evidence.

| Pattern | Meaning used by this skill |
|---|---|
| `ES....` | Common/ordinary share family |
| `EP....` | Preferred share family |
| `D.....` | Debt instrument family |
| `C.....` | Collective investment vehicle family |
| `O.....` | Option family |
| `F.....` | Future family |
| `R.....` | Entitlement/right family; section required for warrant subtype |
| `M.....` | Miscellaneous; route and section required |

Do not decode ungoverned CFI character positions from memory. Preserve the full raw CFI.

Every classification output must also disclose:

```text
cfi_mapping_version = controlled-prefix-v1.1.0
cfi_mapping_scope = partial_controlled_prefixes_not_full_iso_10962
cfi_decode_depth = category_or_group_prefix_only
```

These fields prevent the controlled prefix mapping from being mistaken for a complete ISO 10962 decoder.

### Section rules

Normalize Chinese and English section labels before matching.

| Section signal | Instrument type |
|---|---|
| 普通股 / common stock / ordinary share | `common_share` |
| 特別股 / preferred share | `preferred_share` |
| 臺灣存託憑證 / TDR / depositary receipt | `depositary_receipt` |
| ETF / exchange traded fund | `etf` |
| ETN / exchange traded note | `etn` |
| 認購(售)權證 / warrant | `warrant` |
| 受益憑證 / fund | `fund` unless ETF/ETN evidence is stronger |
| 轉換公司債 / convertible bond | `convertible_bond` |
| 普通公司債 / government bond / bond | `bond` |
| 期貨 / future | `future` |
| 選擇權 / option | `option` |
| 指數 / index | `index` |
| 黃金現貨 / gold spot | `gold_spot` |
| STO / security token | `security_token` with a CFI-derived subtype when safe |

### Conflicts

- Section `普通股` plus `EP....` CFI is a conflict.
- Section `ETF` plus `ES....` CFI is a conflict unless an official exception is documented.
- Mode 9 plus equity classification is a conflict.
- A code-pattern guess that conflicts with section or CFI is ignored and logged.

Conflict categories and effects:

| Category | Typical fields | Effect |
|---|---|---|
| `identity_conflict` | code, ISIN | hard quarantine |
| `classification_conflict` | CFI, route/mode, market, section | hard quarantine |
| `date_semantic_conflict` | issue/listing/registration/maturity date | review; preserve provenance, do not silently quarantine identity |
| `observation_lag` | differing dates from differently updated lanes | review; retain source update dates |
| `noncritical_enrichment_conflict` | industry, remarks | preserve multiple values as warning/evidence |

## 4. Confidence and quarantine

Use these statuses:

- `confirmed_dual_lane`: Chinese and English identity-critical fields agree.
- `confirmed_official_single_lane`: one official lane plus consistent section and CFI.
- `provisional_single_lane`: one official lane but missing a required cross-check.
- `ambiguous`: more than one viable identity candidate.
- `quarantine_conflict`: official fields conflict.
- `quarantine_unknown`: insufficient governed classification evidence.

Reason codes must explain the decision, for example:

```text
MODE_2_TWSE_COLLECTION
SECTION_COMMON_SHARE
CFI_ES_COMMON_SHARE
DUAL_LANE_MATCH
MODE_SECTION_CONFLICT
UNKNOWN_CFI
```

## 5. Current listed-common-stock flag

Set `listed_common_stock_core_flag=true` only when all are true:

1. Instrument type is `common_share`.
2. Mode is 2 or 4.
3. Market evidence agrees with TWSE or TPEx.
4. No identity or classification quarantine exists.

This flag describes a current master subset. It does not prove PIT, survivorship, corporate-action, or backtest readiness.
