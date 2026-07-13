# M8C TAIFEX MIS runtime observation schema

Status: `m8c_01_taifex_mis_bounded_snapshot_runtime_pass_with_caveats`.

M8C-01 observations are compact normalized records from TAIFEX MIS same-origin REST bootstrap plus ephemeral SockJS XHR polling. They are `official_undocumented` and `liveish_intraday_snapshot`; they are not realtime guarantees, streaming feeds, trading signals, public APIs, or AI conversation context.

Required fields: `source_id=TAIFEX_MIS`, `authority_level=official_undocumented`, `timing_class=liveish_intraday_snapshot`, requested product, MIS CID, runtime SymbolID, instrument/session/contract identity, raw `CDate`/`CTime`, conservatively resolved source timestamp, source status/market phase, TAIFEX-specific currentness, normalized field candidates, field provenance, network scope, retained scope, caveats, and `raw_payload_retained=false`.

Field precedence is SockJS `mode=1` initial quote state, exact `getQuoteDetail` fallback, then quote-list fallback. Missing values stay null; malformed values stay null with a caveat; zero is a valid zero. Decimal is used for numeric normalization. `trueValues`, raw QID maps, cookies, SockJS session paths, full option chains, and raw payloads are never returned.

Top-of-book candidate families `101/102/113/114` and `743/744/745/746` are preserved separately. Canonical best bid/ask are populated only when families agree or a directly validated priority exists; otherwise canonical fields are null and `canonicalization_status=top_of_book_field_family_unresolved`.
