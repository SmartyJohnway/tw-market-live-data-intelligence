# Phase H H3-R3 — TPEx EDIS Authenticated Transport Contract

Status: **OWNER-SUPPLIED SOURCE CONTRACT / DORMANT IMPLEMENTATION**
Date: 2026-09-24
Baseline: `7ae13fcdcbe49154814feb31233403d368c63638`

## 1. Source examined

The official TPEx E-Data Shop API Manual is dated **2024-09-02**. The manual
used for this decision was Owner-supplied after being downloaded from the
official TPEx surface at
[the official manual download URL](https://eshop.tpex.org.tw/uploadFile/upload/product/2c92e01394fcf4c7019518bc880f000b.docx).
Its SHA-256 was verified for this review as:

```text
7d9eb39daea22c324b58d6cbb17032bd4200ee430c44ee136ce92018087f30d4
```

No copy of the manual is committed as a runtime/source artifact by this
tranche. H3-I1B code and tests did not persist the manual and did not perform
an authenticated EDIS API or market-data request. This record makes no claim
that the Owner-supplied source file never existed on disk.

## 2. Documented operations

The manual defines two relative operations:

```text
Step 0: /download/getApi?step=0
Step 1: /download/getApi?step=1
```

Both use the API data-download `account` and `pwd`, which the manual explicitly
says differ from normal website login credentials. `lang` is optional and is
documented only as `zh` or `en`. Step 1 additionally takes `fileName` exactly as
obtained from the Step-0 product-file list.

Step 0 successful response is documented as `Text`; its example uses the
Chinese grammar `商品名稱：<product> , 檔案名稱：<file><br/>`. The dormant
transport parses only this conservative Chinese example. Other text is
retained in memory and reported with `list_parse_status=unrecognized_format`.
Text decoding is attempted only when the response declares a charset; without
one, a successful Step-0 body fails closed rather than guessing an encoding.
The transport still scans UTF-8 bytes solely for the manual's exact documented
provider-error strings before considering a response successful. No English
list grammar is inferred.

The manual does not sufficiently specify the successful Step-1 response body
type. The implementation therefore returns bounded Step-1 bytes opaquely. It
does not assume ZIP, TXT, HTML, JSON, or redirect semantics and does not decode,
extract, normalize, or persist the payload.

## 3. HTTP method decision

The parameter sections are headed `POST Parameters`, while both executable
cURL samples explicitly use `curl --location --request GET` and place
parameters in the query string. This tranche follows the executable samples:

```text
implemented method = GET
POST = not implemented
```

This inconsistency is retained as a future live-verification question rather
than silently reconciled. A future authorized provider probe may reopen the
decision if official behavior contradicts the samples.

## 4. Host and redirect boundary

The manual uses `{網站位置}` rather than binding a production host. Public TPEx
material identifies `https://intd.tpex.org.tw` as a host candidate, but it has
not been live-verified for this API. Each call therefore requires an explicit
HTTPS origin; there is no default host. Production host binding remains:

```text
NOT LIVE VERIFIED
```

The dormant default HTTP executor explicitly disables redirects. A 3xx result
fails closed and does not disclose or follow the `Location` value. This avoids
forwarding query credentials to an unexpected host while redirect behavior is
unverified.

## 5. Bounds and secret handling

Each invocation makes at most one GET, requires a finite positive timeout and a
positive maximum response size, reads at most `max_response_bytes + 1`, and
does not retry, poll, paginate, schedule, or discover additional files. The
transport is injectable so tests make zero network calls.

Credentials are necessarily present in the transient GET query required by the
official samples. The transport does not return, hash, persist, log, or include
them in result metadata. It translates transport exceptions to generic
sanitized results, detects a credential echoed in a response before exposing
the body, and excludes the request URL from public results and errors.

## 6. Documented provider error handling

The implementation matches the documented Chinese and English system
messages covered by its mapping and tests for missing credentials/step,
inactive or unconfirmed account, incorrect password, API access disabled,
absent subscription, and Step-1 filename/product/subscription/download-limit/
link-expiry conditions. These become deterministic access/provider error
codes, never H3 market-coverage states. Step 0 additionally maps
`尚無期限內的 API 檔案` to `no_valid_api_subscription`. This is coverage of the
mapped documented messages, not a claim that every possible provider error is
classified.

An unrecognized non-success response remains `provider_response_unclassified`.
HTTP status alone is not mapped to password, filename, or subscription
semantics; in particular, HTTP 200 is still checked for documented provider
messages first. A 2xx Step-1 response explicitly declared textual must decode
under its declared charset before it can be returned as opaque bytes; an
undecodable textual response fails closed as `provider_response_unclassified`.
No fallback charset is guessed.

## 7. Explicitly unresolved

```text
public official host candidate = https://intd.tpex.org.tw
production host binding = NOT LIVE VERIFIED
Step-1 successful payload type = NOT FULLY SPECIFIED
authenticated live behavior = NOT VERIFIED
fresh-install arbitrary last-20-session continuity = NOT PROVEN
H3 runtime route = BLOCKED / INACTIVE
```

This record is additive. It does not rewrite the historical H3-R1 or H3-R2
decisions and does not establish H3 source authority or activation.
