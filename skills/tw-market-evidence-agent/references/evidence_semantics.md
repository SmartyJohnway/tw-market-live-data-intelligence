# Evidence semantics

Baseline SHA: `d6b83313bb301e652ae82b8583d73d2aaa1d753e`

## Timing taxonomy

- `live`: verified live stream only; currently not a general guarantee.
- `liveish_intraday_snapshot`: current-ish source observation; not zero-latency realtime.
- `current_bounded_observation`: bounded execution result with retrieval provenance.
- `retrieved_snapshot`: data as retrieved at `retrieved_at`; `retrieved_at` is not exchange event time.
- `completed_session_eod`: official completed-session OHLCV; not intraday current price.
- `official_settlement`: derivatives settlement context; not spot current price.
- `historical_series`: past series; may be unadjusted.
- `fixture_only`: test/regression evidence only, not market state.
- `unknown`: insufficient timing evidence.

## Source authority classes

`official_exchange_current`, `official_exchange_eod`, `official_government`, `official_issuer`, `credential_gated_provider`, `external_validation_only`, `manual_operator_evidence`, `fixture`, and `derived_calculation` are defined in the JSON contract. Fixture evidence is never current market evidence. Derived calculations must cite exact input evidence and method.

## Calculation semantics

Price change and percentage change require aligned inputs. `unadjusted_return` is a price return only, not total return; dividends, splits, and corporate actions can change interpretation. Settlement comparisons require explicit spot/derivatives timing alignment.

## Availability semantics

AI-facing capability names in F1 are operation contracts, not callable Phase C tools. Underlying repository producers may exist and may be fixture-validated or implemented with caveats, but network-required producers remain disabled by default and require M8R-03D controlled execution authorization.
