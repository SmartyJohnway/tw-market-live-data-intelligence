# Target Config Schema Draft

This document outlines a proposed update to the `config/market_targets.json` schema.
This is a draft designed during milestone M2E-01 and intentionally not yet implemented to ensure existing live probes remain stable. It is intended for implementation in a future milestone (e.g., M2E-02).

## Rationale for Update
The current `market_targets.json` format categorizes arrays of symbols by loose group names (e.g., `twse_large_caps`, `tpex_stocks`) and parallel lists of string identifiers for different sources.
This structure makes it difficult to reliably map a single asset's canonical taxonomy class or maintain robust cross-source symbol mappings without index matching across parallel arrays.

## Proposed Schema

The new schema shifts to a dictionary where the primary key is a canonical internal identifier (or the raw local symbol), and the value is an object explicitly defining the asset's taxonomy and source-specific formats.

### Example Structure

```json
{
  "2330": {
    "canonical_target_class": "twse_common_stock",
    "name": "台積電",
    "symbol_formats": {
      "twse_mis": "tse_2330.tw",
      "yahoo": "2330.TW",
      "twse_openapi": "2330",
      "tpex_openapi": null,
      "finmind": "2330"
    }
  },
  "8069": {
    "canonical_target_class": "tpex_common_stock",
    "name": "元太",
    "symbol_formats": {
      "twse_mis": "otc_8069.tw",
      "yahoo": "8069.TWO",
      "twse_openapi": null,
      "tpex_openapi": "8069",
      "finmind": "8069"
    }
  },
  "TAIEX": {
    "canonical_target_class": "twse_index",
    "name": "TAIEX",
    "symbol_formats": {
      "twse_mis": "tse_t00.tw",
      "yahoo": "^TWII",
      "twse_openapi": null,
      "tpex_openapi": null,
      "finmind": null
    }
  }
}
```

### Key Changes
1. **Object-based Asset Representation:** Moves away from parallel arrays in categorized groups.
2. **`canonical_target_class`:** Explicitly references the taxonomy defined in `TARGET_TAXONOMY.md`.
3. **`symbol_formats` Dictionary:** Groups all source-specific formats for a single asset together. Missing or unsupported sources are explicitly marked as `null`.

### Migration Strategy (For Future Milestone)
1. **Update Probe Scripts:** Modify `scripts/run_all_probes.py` and individual probe scripts (e.g., `scripts/probe_twse_mis.py`) to parse the new dictionary structure.
2. **Backwards Compatibility:** Ensure the new parsing logic gracefully handles missing keys or `null` values by skipping unsupported probes for that asset, rather than throwing errors.
3. **Unit Tests:** Add comprehensive unit tests in `tests/unit/test_market_targets_config_schema.py` to validate schema compliance before deploying the configuration change.
