# Lifecycle Contract

## Contents

1. Event model
2. Date semantics
3. Source routing
4. Product-specific requirements
5. Completeness

## 1. Event model

Represent history as append-only events:

```json
{
  "event_type": "emerging_terminated",
  "effective_date": "2026-03-30",
  "date_raw": "115年3月30日",
  "calendar": "ROC",
  "market": "emerging",
  "reason_code": "transfer_to_twse",
  "source_url": "https://www.tpex.org.tw/...",
  "evidence_status": "official_explicit"
}
```

Do not overwrite a prior state when a security changes market.

Controlled event types include:

```text
public_issued
gisa_registered
gisa_terminated
emerging_registered
emerging_suspended
emerging_resumed
emerging_terminated
tpex_listed
tpex_suspended
tpex_resumed
tpex_delisted
twse_listed
twse_suspended
twse_resumed
twse_delisted
issued
matured
last_trading
early_terminated
name_changed
code_changed
merged_or_converted
```

## 2. Date semantics

Never collapse these fields:

- `announcement_date`
- `issue_date`
- `listing_date`
- `registration_date`
- `last_trading_date`
- `maturity_date`
- `termination_effective_date`
- `contract_termination_date`

Normalize ROC dates such as `1150624`, `115-06-08`, and `115/06/23` to Gregorian ISO, while retaining the raw value.

Use three-state values:

- ISO date when supported.
- `not_applicable` when the event cannot apply.
- `unknown` when it may apply but evidence is missing.

## 3. Source routing

| Event | Preferred source |
|---|---|
| TWSE company delisting | TWSE terminated-listing table |
| TPEx company delisting | TPEx terminated-OTC table |
| Emerging termination/transfer | TPEx market announcement |
| ETN expiry/termination | TWSE or TPEx ETN termination table |
| ETF termination | Exchange announcement and ETF information center |
| Warrant scheduled maturity | Warrant basic-data endpoint |
| Warrant early termination | Exchange/MOPS announcement and attachment |
| Suspension/resumption | Exchange market announcement |

## 4. Product-specific requirements

### Warrant

Keep:

```text
scheduled_maturity_date
actual_maturity_date
last_trading_date
scheduled_termination_date
actual_termination_date
early_termination_flag
termination_reason
underlying_code
issuer_code
```

### Bond and NCD

Keep issue and maturity dates separately. Do not use maturity as a delisting date unless an official event explicitly equates them.

### ETF and fund

Keep fund contract termination separate from exchange termination. Preserve manager and product identifiers when available.

### Market transfer

An emerging termination caused by TWSE listing is two events, not one mutation:

```text
emerging_terminated(reason=transfer_to_twse)
twse_listed
```

## 5. Completeness

Report lifecycle completeness as:

- `complete_for_requested_events`: every requested event has explicit official evidence or is not applicable.
- `partial`: at least one requested event is unknown.
- `current_identity_only`: only current official identity is established.
- `conflicted`: official event evidence disagrees.

Absence from an announcement search is never proof that an event did not occur.

## 6. Implemented adapter boundary

The bundle parses supplied official HTML captures with:

```text
parse_twse_delisted.py
parse_tpex_delisted.py
parse_tpex_announcement.py
parse_etn_termination.py
```

`parse_tpex_announcement.py` requires an explicit controlled event type; it does not guess an event solely from prose. `parse_etn_termination.py` emits separate delisting, maturity, and last-trading events when those dates are present. Use `merge_lifecycle_events.py` for append-only deduplication.

Active retrieval and interpretation of linked PDFs or announcement attachments remain adapter/manual-review work. Until a capture is successfully parsed, describe the capability as validating or modeling supplied lifecycle evidence, not guaranteed automatic enrichment.

### Header and calendar safety

- TWSE's official terminated-listing table uses `終止上市日期`, `公司名稱`, and `上市編號`; `上市編號` is a governed security-code alias.
- Recognizable HTML with no governed lifecycle header is `schema_drift`, not a valid empty result. CLI adapters must return a nonzero exit code and structured issue details.
- Detect ROC forms including `114年07月24日`, `114/07/24`, `114-07-24`, and seven-digit compact dates. Preserve `date_raw` and never infer `Gregorian` merely because a ROC separator was not `/`.
