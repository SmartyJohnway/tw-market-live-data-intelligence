# Post-v1.5 — v1.5.1 Final-Candidate Assembly / Release-Gate Record

Date: 2026-11-03 (Asia/Taipei)
Status: **IN PROGRESS / PRE-COMMIT FINAL-CANDIDATE GATE**
Base HEAD: `b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c`
VERSION remains: `1.5.0`

## FC-RG001 — H3 strict-TLS regression expectation drift

First valid isolated `release-blocking-ci` run selected current release-blocking tests and returned 1928 PASS / 4 skipped / 2 FAIL. Both failures were in `tests/unit/test_phase_h_h3_i2a_twse_stock_day_adapter.py` and asserted that strict-policy `_default_http_get` receives `ssl_context is None`.

This expectation conflicts with accepted RMA-D001 authority. RMA-7 CLOSED_PASS requires strict and compatibility production TLS to use the governed bundled certifi CA file, retain certificate and hostname verification, and exercise an explicit verified SSL context across the 23-source inventory. `test_rma_d001_deterministic_tls.py` already enforces the same strict-context semantics.

Disposition: **FINAL-CANDIDATE TEST-AUTHORITY RECONCILIATION REQUIRED**. Runtime behavior is not changed. The two stale H3 assertions may be updated to require an explicit verified strict SSLContext and single-dispatch/no-retry behavior, followed by targeted and full release-blocking retest.

## FC-RG001 retest disposition

Targeted H3 + D001 TLS regression passed **70/70** after test-only reconciliation. The same isolated C-drive candidate then passed `release-blocking-ci` attempt-03. Runtime product bytes were unchanged by FC-RG001.

## FC-RG002 — legacy `full-non-network` collection portability debt

Supplemental `full-non-network` did not reach test execution on Windows: one Phase-J acceptance module used locale-default `Path.read_text()` and failed to decode UTF-8 under cp950, while another legacy A6 harness imports POSIX-only `fcntl`. These paths are outside the governed `release-blocking-ci` selection and are not new v1.5.1 runtime failures. They are preserved as non-blocking legacy-profile debt; no product or historical-harness repair is authorized by final-candidate assembly.
