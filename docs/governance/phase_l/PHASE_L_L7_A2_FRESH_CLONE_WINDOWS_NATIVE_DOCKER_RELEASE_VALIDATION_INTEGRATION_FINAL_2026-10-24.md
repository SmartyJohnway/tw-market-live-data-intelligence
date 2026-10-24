# L7-A2 fresh clone / Windows / Native / Docker validation integration

Disposition: `L7_A2_FRESH_CLONE_WINDOWS_NATIVE_DOCKER_RELEASE_VALIDATION_INTEGRATION_PASS`. **TECHNICAL PASS; OWNER ACCEPTANCE PENDING.**

Canonical entry `0e903ba042df7fed63f2c0ccd1c82dd5a28b62b5`, tree `910803236875dbfbcf52efb166f1ce2eafd514e7`. Preserved blocked checkpoint `cd90403f66948618510632806627da3f78f27a62`. Independently accepted compatibility repair `faba8c219426b20665b3fc94c090f836d6fe3c0c`, tree `fb4579b94873052b54dc402d5ebe6700eb4320ca`.

Final tested implementation `510625c8e81e629e2c902b17949aa155abfe78b6`, tree `e0450583689bf87d6329e226e5a66012006ea716`. The final candidate is its evidence/governance-only sealing child. Its exact commit/tree/parent and committed-byte manifest verification are recorded after commit in `C:\twmarket_temp\l7-a2\continuation\committed-candidate-receipt.json` and the PR body. The tested implementation tree is not mislabeled as the final candidate tree.

## Acceptance

- Actual GitHub fresh clone, exact unpublished local candidate fetch, clean source and no inherited runtime/state; packaged consumer runs outside the checkout.
- Canonical A1 gate: **1895 passed, 0 failed, exactly four contracted historical witness skips**, no unexpected skips/xfails or guard denials; exact selection ledger unchanged.
- New Native validation ZIP: `TW-Market-1.0.0-windows-x64.zip`, SHA-256 `a05d4e39da2f80c409749f66493a93658047950e29348a96986de53280f8c499`, 338 members / 49 unchanged wheels, ProductVersion `1.0.0`. Structural/tamper checks, offline bootstrap and init idempotence, pre-init read-only checks, lifecycle, doctor immutability, exact-six interactive MCP, APP_ROOT immutability and A→B same-state relocation all PASS. Portable first-party path/secret/state scans fail closed; only existing exact upstream wheel exceptions remain.
- Genuine fresh **Windows11 Enterprise build 26100 x64** Sandbox: no pre-existing HOME/STATE/Python/Git, no host checkout/profile/venv mapping. The same exact ZIP is hash-verified inside guest; full Native lifecycle/relocation/exact-six passes with actual exit **0**. Networking is disabled. Host or GitHub windows-latest is not substituted for this proof.
- Docker pinned accepted Alpine base, Linux/amd64 / Python3.13.17 / unchanged 48-wheel closure. A `sha256:e18d0913c7e707e54ec909d3c556de4b4e361d084aab2195260b2a1e610d431d` → B `sha256:e6bf6ae779c3dab4a50dbf2ce4fb4221a35307a60b2db8921e01a4220eca59df` replacement preserves installation and all durable business-state hashes; RootFS/application hashes match. Fresh volumes, explicit/idempotent init, read-only nonroot runtime, loopback host exposure, health/doctor/MCP startup and captured guard logs PASS. Only exact `tw-market-l7-a2-*` resources are used; no unrelated cleanup.
- Windows workflow supports manual dispatch and `windows-smoke` label opt-in, retained across synchronize/reopen; unlabeled expensive jobs are rejected. Release validation is pre-publication/manual, uses canonical A1 gate and current Native/Docker engines, has read-only token permissions and no release/tag/registry publication. Static validation plus real local integration is the authorized A2 proof; hosted RC execution remains later work.

## Prerequisite and boundaries

The full official CPython MSI prerequisite did not complete in two discarded guest setup attempts. The final disposable guest instead uses **official CPython NuGet 3.13.9**, documented by [CPython](https://docs.python.org/3.13/using/windows.html#the-nuget-org-packages), with official catalog SHA-512, package SHA-256 and Python Software Foundation Authenticode verification. It is extracted only into the guest acceptance root; no host installation, runtime version change, dependency declaration change or final A3 support decision occurs.

Setup acquisition/verification (GitHub, official CPython/NuGet, pinned base metadata) is recorded separately. Product live-provider requests, market acquisition, Security Master updates, refresh and background market polling are **0**. Localhost health/readiness traffic is allowed and recorded. Process guards cover Python/inherited Python/Node and the Docker exact native identity allowlist; no OS firewall or whole-host network claim is made.

The earlier host TEMP incident remains immutable and is not erased by clean reruns. All continuation TEMP/TMP/basetemp roots are explicit under A2. Failed/intermediate attempts are retained and never relabeled PASS: incorrect old MCP path/readiness predicates, deadline failures during concurrent work, the formerly rejected local `uname -p` probe, incomplete MSI provisioning and the guest wrapper's missing exit status. The final runs stand independently; no timeout or product contract was weakened. The fixed uname allowance is exact argv, anchored to the pinned base binary, with all other native children still denied and negative tests retained.

## Governance

L7-GAP-05/06/07 are CLOSED. GAP-20 is `RETAINED_NONBLOCKING_HISTORICAL_LIMITATION_WITH_CURRENT_A2_REPLACEMENT_PROOF`; no historical A5 digest is manufactured. Only EXIT04/05/06/07 gain A2 PASS. Existing A1 EXIT01/02/03/27 remain preserved; exact-six/public-contract checks are `PASS_AS_PRESERVATION`, `FINAL_L7_ACCEPTANCE_DEFERRED`.

L6 remains CLOSED. L7-A0/A1 remain OWNER-ACCEPTED AND MERGED. A2 is TECHNICAL PASS / OWNER ACCEPTANCE PENDING. A3+, stable release/publication, merge and Phase M remain NOT AUTHORIZED. Phase L is NOT CLOSED. DEFAULT_CI/FULL_NON_NETWORK historical diagnostics are not rerun or represented as green.

The [final evidence manifest](acceptance_runs/l7-a2-20261024T133622Z-final/manifest.json) seals the new run. Both earlier blocked and compatibility-repair evidence directories and the original blocked report remain unchanged. No ZIP, venv, image export or Sandbox image is committed.
