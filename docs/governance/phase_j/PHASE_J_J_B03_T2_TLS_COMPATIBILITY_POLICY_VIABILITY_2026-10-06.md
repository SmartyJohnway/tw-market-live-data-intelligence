# J-B03-T2 Existing TLS Compatibility Policy Viability

**Decision:** `J_B03_T2_EXISTING_COMPATIBILITY_POLICY_VIABLE`

PR #305 is merged at `db0c66d0def18442a7428492fab17f5116df14e7`, tree `4a5dc9c52319132e049d5af9081b73c129c34b6e`. The T1 diagnosis remains `J_B03_T1_DIAGNOSIS_PROXY_OR_TLS_INTERCEPTION_DIFFERENCE` (HIGH confidence).

## Policy and TLS-only result

The repository policy keeps `strict` as default. Its explicit `compatibility` mode uses `ssl.create_default_context()` and removes `VERIFY_X509_STRICT` when available. It leaves `CERT_REQUIRED` and hostname checking enabled. `unsafe-explicit` is not used or authorized.

Before connecting, the test asserted an `SSLContext`, `verify_mode=CERT_REQUIRED`, `check_hostname=True`, and `VERIFY_X509_STRICT` absent. All assertions passed. One raw TLS handshake to `www.tpex.org.tw:443` with matching SNI succeeded using TLS 1.2. The peer certificate was issued by TWCA, had SAN `www.tpex.org.tw`, and was within its validity period. No HTTP bytes were sent: GET=0, HEAD=0, POST=0, source-shape acquisition=0.

No ESET-issued certificate was observed in this T2 handshake. T1's ESET filter observation remains historical evidence; ESET and machine trust were not modified.

## Blast radius and next step

The shared `_fetch_official_payload` helper is used by Phase G material disclosure/monthly-revenue execution and H1 TPEx attention; the H2 acceptance runner also reuses it. A global change would affect accepted Phase G and existing H1 behavior. Phase I I3 uses a separate transport. Do not change the shared helper globally to address only this H1 source.

T1 local certifi was `2026.2.25`; the repository lock specifies `2026.7.22`. No certifi-backed production transport was added. TLS-policy viability does not prove the H1 source response contract and does not resume J-B03 A1. A new, explicit authorization is required for one fresh source-shape GET using compatibility policy, retry 0.

J-B03 remains HOLD, J-B04 remains BLOCKING, Phase J remains NOT STARTED, and MCP remains six tools.
