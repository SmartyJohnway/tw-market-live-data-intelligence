# J-B03-S2D — TPEx `tpex_cmode` Marker Semantics Authority

**Disposition:** `J_B03_S2D_HOLD_MARKER_AUTHORITY_NOT_PUBLISHED`

**Evidence level:** `LEVEL 1 — INFERENCE ONLY`

## Finding

The observed source marker is fullwidth capital Y `Ｙ` (`U+FF39`, UTF-8 `efbcb9`) in `SuspensionOfTrading`. Official [data.gov.tw dataset 11736](https://data.gov.tw/dataset/11736) publishes the dataset title, the field label `停止交易`, daily cadence and ODGL 1.0 authority. It does not publish a codebook mapping U+FF39 or ASCII `Y` to an affirmative value for this field.

The TPEx OpenAPI portal, Swagger document and human query page returned HTTP 403 through the documentation research path, so no field enum, example, or deterministic API-to-display mapping was available. The located TPEx IP-feed specification is a different technical feed and has no established relation to `tpex_cmode`; it is not used as marker authority. The repository's frozen H1 record establishes source/dataset routing and field inventory, but does not define marker values. The S2C observation is source evidence, not semantic authority.

`unicodedata.normalize("NFKC", "Ｙ") == "Y"` is true as a Unicode technical fact. It does not establish business meaning. Cross-field repetition of U+FF39 is likewise only an inference absent an official shared convention. Accordingly, `SuspensionOfTrading == "Ｙ"` is **not authorized** to normalize to affirmative stopped trading.

Blank remains undefined and does not mean “not stopped.” A target-absent row does not mean normal trading.

## Safe native-evidence fallback

Classification: `SAFE_NATIVE_EVIDENCE_FALLBACK_POSSIBLE`.

The product may quote the exact source field, marker and date with a citation and an explicit caveat, for example:

> TPEx 的「停止交易」欄位目前標示為「Ｙ」；本系統尚未取得足夠官方欄位代碼文件，因此不將該標記自動正規化為肯定停牌狀態。

This reports the source-native value without interpreting it as a boolean. It requires exact target/date binding and preserved citation. No runtime or schema change is authorized here.

## State and boundary

- `H0-SRC-01E` = OPEN; `H0-SRC-02` = OPEN.
- J-B03 = HOLD; J-B04 = BLOCKING; Phase J = NOT STARTED.
- Market-data GET/HEAD/POST = 0. No `tpex_cmode` payload or CSV was downloaded.
- No production, schema, catalog, routing, registry, activation or MCP change; MCP remains 6.
- `data/` was untouched.

See the adjacent JSON for the official-source inventory, access results, evidence levels and exact marker representations.
