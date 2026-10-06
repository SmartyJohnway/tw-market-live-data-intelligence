# J-B03-T1 TPEx TLS Transport Diagnosis

**Classification:** `J_B03_T1_DIAGNOSIS_PROXY_OR_TLS_INTERCEPTION_DIFFERENCE`

**Confidence:** HIGH

## Client path and result

The earlier shape-probe used Python 3.13.7 `urllib.request.urlopen` with its default strict HTTPS context, backed by OpenSSL 3.0.16. The repository production helper uses the same standard-library `urllib` path and supplies no explicit SSL context. The captured exception was `urllib.error.URLError` wrapping `ssl.SSLCertVerificationError`; the exact verification error was `Missing Subject Key Identifier` (verify code 86 on strict reproduction).

## Trust-path comparison

- Windows 10 Schannel `SslStream`, SNI `www.tpex.org.tw`: strict TLS 1.2 PASS. The peer certificate named `ESET SSL Filter CA` as issuer; the matching self-signed CA is present in CurrentUser and LocalMachine Root stores.
- Python default SSL context: FAIL, verify code 86 `Missing Subject Key Identifier`.
- Python `ssl.create_default_context(cafile=certifi.where())`: strict TLS 1.3 PASS, but it received a different peer certificate issued by TWCA. Its hostname/SAN and validity dates matched `www.tpex.org.tw`.
- Local OpenSSL 3.0.18 `s_client -verify_return_error`: FAIL with self-signed certificate in chain; its configured default CA file/directory paths do not exist.

No HTTP proxy or CA environment override was found. WinHTTP and current-user Internet Settings also reported direct access/no proxy. DNS-only lookup returned TPEx addresses while the Windows socket resolver/cache returned `172.65.90.67` and `.66`; the cause of this resolver difference is unknown.

Together, the different certificates and the installed ESET-labeled root show client/trust-path-dependent TLS filtering. The evidence does not show that the TPEx endpoint certificate is generally invalid. The Python default path rejects the ESET-issued chain on OpenSSL's missing-SKI check.

## Recommendation and boundary

In a separate remediation tranche, evaluate a strict certifi-backed SSL context for the `urllib` production client, or another supported strictly validating backend. Keep certificate and hostname verification enabled. Confirm dependency and TLS-only behavior before seeking fresh bounded source-acquisition authorization.

T1 performed zero market GET, POST, or HEAD requests; it sent no HTTP bytes and persisted no payload. Five TLS handshakes were attempted. No client, CA, trust store, source route, or product authority was changed. J-B03 remains HOLD, J-B04 remains blocking, and Phase J remains not started.
