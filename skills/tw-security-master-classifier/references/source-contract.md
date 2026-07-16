# Official Source Contract

## Contents

1. Authority layers
2. TWSE ISIN lanes
3. OpenAPI enrichment
4. Lifecycle evidence
5. Acquisition states
6. Provenance and joins

## 1. Authority layers

Use official sources as complementary evidence, not interchangeable replacements.

| Layer | Purpose | Identity grain |
|---|---|---|
| A. TWSE ISIN | Security identity, ISIN, CFI, route, section, names, issue/listing fields | Security/issuance |
| B. TWSE OpenAPI | Listed issuer, warrant, ETF/fund, and product enrichment | Issuer or product |
| C. TPEx OpenAPI | OTC, emerging, GISA, warrant, bond, and product enrichment | Issuer or product |
| D. Event sources | Listing termination, OTC termination, emerging termination, maturity, last trading, and reasons | Lifecycle event |

Do not allow a company-level record to overwrite a security-level ISIN record. One issuer can have multiple securities.

## 2. TWSE ISIN lanes

`C_public.jsp` and `e_C_public.jsp` are parallel official observations.

- Use Chinese lane for Chinese name and Chinese headings.
- Use English lane for English name and English headings.
- Compare ISIN, code, CFI, market, and dates across lanes.
- Join by ISIN, never by row order.
- Do not permanently designate one lane as the winner for all fields.
- A single-lane result may be `provisional_single_lane`; it cannot be `confirmed_dual_lane`.

`strMode` is a route or collection, not a complete instrument type:

| Mode | Collection |
|---:|---|
| 1 | Public-issuing, unlisted and non-OTC securities |
| 2 | TWSE-listed securities; mixed product sections |
| 3 | Listed and OTC bonds |
| 4 | TPEx-listed securities; mixed product sections |
| 5 | Emerging securities |
| 6 | Futures and options |
| 7 | Open-ended securities investment trust funds |
| 8 | GISA equities |
| 9 | Registered gold spot |
| 10 | Foreign-currency NCD |
| 11 | Domestic indices |
| 12 | Security token offerings |

Always capture the page title at runtime. Quarantine an unexpected title instead of trusting the numeric mode alone.

## 3. OpenAPI enrichment

- Treat `t187ap03_*` company datasets as issuer-level enrichment.
- Treat warrant, fund, ETF, ETN, bond, and other product datasets as product-level enrichment.
- Do not assume OpenAPI contains ISIN.
- Join issuer data by code and market, then cross-check name and observation date.
- Join product data by security code and market, then cross-check name, issuer, and relevant dates.
- Respect the dataset's declared update frequency. A monthly company or fund export is not a daily status authority.

## 4. Lifecycle evidence

Prefer structured termination and expiry tables. Use announcements when no complete table exists.

Evidence order for an event:

1. Structured exchange termination or expiry table.
2. Exchange announcement with explicit effective date and code.
3. Exchange-hosted announcement attachment.
4. MOPS issuer announcement linked from an exchange source.

Never derive a formal event date from the date a record disappeared or moved between snapshots.

## 5. Acquisition states

Every fetch must end in one of these states:

- `data`: expected payload and schema markers found.
- `security_block`: official site returned a security denial page.
- `captcha`: interactive verification is required.
- `empty_valid`: expected schema is present with zero data rows.
- `schema_drift`: response is data-like but required markers changed.
- `semantic_error`: JSON parsed but contains an error signature or lacks semantic records.
- `decode_failure`: raw bytes were obtained but key fields cannot be decoded safely.
- `http_error`: non-success HTTP result.
- `network_error`: DNS, TLS, connection, or timeout failure.
- `redirect_rejected`: redirect target is outside the HTTPS official-host allowlist.
- `rejected`: requested URL or source identifier violates the source contract.

Never convert `security_block`, `schema_drift`, or `decode_failure` to an empty dataset.

For JSON probes, keep these dimensions separate:

```text
transport_success
payload_parseable
schema_valid
semantic_data_present
```

A parseable object such as `{"error":"rate limit"}` is not data. Apply the dataset's `payload_contract` from the manifest. Validate the requested URL and every redirect target against the HTTPS official-host allowlist, then record `requested_url`, `final_url`, and `redirect_count`.

For Chinese HTML, retain raw bytes. Try declared encoding and controlled candidates (`cp950`, `big5`, `big5hkscs`, `utf-8`, `utf-8-sig`). A replacement character in code, ISIN, or CFI is a quarantine condition.

## 6. Provenance and joins

Persist at least:

```text
source_family
source_lane
source_url
str_mode
source_updated_date_raw
source_updated_date
observed_at
http_status
content_type
acquisition_method
raw_payload_sha256
parser_version
row_hash
```

Join rules:

| Relationship | Primary key | Required cross-check |
|---|---|---|
| Chinese ISIN to English ISIN | ISIN | code, CFI, date |
| ISIN to issuer OpenAPI | code + market | name, observation date |
| ISIN to product OpenAPI | security code + market | name, product family |
| ISIN to termination table | code + event market | name, event date |
| Warrant to early-termination announcement | warrant code | issuer, scheduled dates |
| Former name to issuer | company code + time | unified business number when available |

If a join is ambiguous, return all candidates and `resolution_status=ambiguous`.
