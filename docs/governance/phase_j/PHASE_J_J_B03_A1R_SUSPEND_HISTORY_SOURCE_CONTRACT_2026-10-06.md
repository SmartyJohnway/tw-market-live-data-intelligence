# J-B03-A1R TPEx Suspend-History Source Contract

**Disposition:** `J_B03_A1R_HOLD_SEMANTIC_INSUFFICIENCY`

## Source and transport

Static authority matched the selected source: TPEX, `governed_fallback`, `eligible`, not runtime-executable, ODGL 1.0, with an empty route activation-blocker list. The official endpoint is `https://www.tpex.org.tw/openapi/v1/tpex_spendi_history`.

One authorized GET used the repository `compatibility` policy. Before connection, assertions passed for `SSLContext`, `CERT_REQUIRED`, `check_hostname=True`, and `VERIFY_X509_STRICT` absent. The TLS handshake and HTTP request succeeded (200, `application/json`); the endpoint did not redirect. The response was streamed under the previously accepted 4 MiB I3 bound. It was 79,602 bytes with SHA-256 `4e3747a4a27c1e45542ce476ff7ccd0384e5c420e9f2d5bbfd9257b9cc48e6a2`. Raw response bytes were transient and were not committed.

## Observed shape

The JSON root was an array of 362 objects. Union and intersection were the same eight fields: `CompanyName`, `Date`, `DateOfResumedTrading`, `DateOfSuspendedTrading`, `SecuritiesCompanyCode`, `Serial`, `TimeOfResumedTrading`, and `TimeOfSuspendedTrading`. Every documented candidate field was present in every row.

All security codes were JSON strings: 352 numeric strings and 10 alphanumeric/other strings; lengths were 4 (30), 5 (10), and 6 (322), with no observed leading zeros. Each of 181 codes appeared exactly twice. `Serial` was a numeric string on every row and unique in this response (362 distinct values); this does not establish correction or supersession semantics.

Each of the four event date/time fields was a string on all 362 rows, with 181 blank strings and no null or missing values. The nonblank time values were all classified as six-digit numeric / HHMMSS-like; an example was `080000`. Nonblank date examples included `1150618`, `1150312`, `1150622`, and `1150313`. The single-pass analyzer left every nonblank event date in an undifferentiated `other_string_pattern` bucket and did not validate its calendar convention. `Date` was a string with observed example `115`; no publication-date interpretation was made.

## Semantic boundary and decision

The response supports a safe event-only design direction: populated suspension fields can represent a source-recorded suspension event, and populated resumption fields can represent a separately reported resumption event. Two rows for one exact code are valid historical-event multiplicity; the rows were not linked into a lifecycle using `Serial` or text similarity.

Blank resumption fields prove neither resumed nor still suspended. Missing target rows prove neither normal trading nor current state. The source alone does not establish present tradeability, and local date comparison cannot establish that a suspension ended.

A1R remains HOLD because the full event-date value grammar and calendar validity were not established in the one response analysis. The observed seven-digit examples are not enough to claim that every nonblank date follows that grammar. The authorized GET is consumed; there was no retry or other market request. No A2 implementation, route activation, or production change was made.

PR #304 HOLD, PR #305 T1 diagnosis, and PR #306 T2 compatibility viability remain prior evidence. J-B03 remains HOLD, J-B04 remains BLOCKING, Phase J remains NOT STARTED, and MCP remains six tools.
