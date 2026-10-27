# Phase L / L7-A6-R1 — Stable RC Source Contract

Disposition: `L7_A6_R1_RC_SOURCE_CONTRACT_CANDIDATE`.
Independent review: **PENDING**.
Authorized on 2026-10-27; completion verification continued on 2026-10-28 Asia/Taipei.

Authority: `USER_CHAT_2026-10-27_L7_A6_R1_RC_SOURCE_CONTRACT_AUTHORIZATION_1`.
Operation: `L7-A6-R1-RC-SOURCE-CONTRACT-20261027-01`.
The MCPB retention, A4 wheelhouse read, digest correction, RECORD canonicalization,
exact-member text provenance and semantic-classifier continuation authorities are
bound in the evidence package. Their earlier fail-closed stops remain historical.

## Exact source identity

- Entry main: `f03ce1d48d9d018b050755d10a4e7489335fe964`.
- Entry tree: `0a2128da39e8759d47344ed253ae1c784841ed2b`.
- Entry parents: `32fc28fc33cb19337bf8d8a2d2e857f978b31b4c` and
  `75bb8053d4bd69ce2c07e7036d044866987d10d8`.
- Branch: `phase-l/l7-a6-r1-rc-source-contract`.
- Implementation commit: `f2eae235ce8ee2dab47e362dc1044bf021a78f2e`.
- Implementation tree: `301f3ae75062bb1d509c1fc4fbcc01d90f43219a`.
- Implementation parent: exact entry main above.

The implementation is one coherent RC-contract/MCPB candidate. No standalone
MCPB commit, history rewrite, push, PR, merge, tag, release or Registry publication
was performed. The subsequent local commit contains this report and evidence only.

## Additive contract and publication inputs

The Draft 2020-12 schemas are `l7_rc_source_contract.v1` and
`l7_publication_manifest.v1`. Governed object levels reject unknown properties.
The existing V1 release manifest schema/builder remain byte-unchanged for their
accepted readiness-smoke role.

`build_l7_rc_source_contract.py` requires a clean committed source, derives HEAD
commit/tree and tracked VERSION 1.5.0, and hashes the governed source files,
artifact policy, dependency locks and SBOM. Instances are written externally.
`build_l7_publication_manifest.py` validates explicit source/artifact/evidence
bindings, requires source/product agreement, verifies supplied file bytes/hashes,
checks checksum sidecars/SBOM identity and rejects missing, duplicate, undeclared,
malformed, placeholder or mismatched inputs. R1 exercised only synthetic final
manifest fixtures.

`MANIFEST_SELF_HASH_EXTERNAL_BINDING`: no manifest requires its own hash inside
itself. Its final byte identity is bound externally by later A6/A7 evidence.
No source-contract instance describes the commit containing that same instance.

The artifact-set policy requires Native ZIP + SHA-256 sidecar, Windows MCPB +
SHA-256 sidecar, first-party SBOM export and the typed L7 publication manifest as
PUBLICATION_ASSET. Docker is VALIDATION_ONLY, with registry publication false.
GitHub source ZIP/tarball are PLATFORM_GENERATED and bound through the eventual
tag/source relationship. Historical v1.0.0 MCPB/sidecar and V1 manifest remain
HISTORICAL_ONLY. Publisher cryptographic signing authority is NOT_ESTABLISHED.

Canonical filenames include `TW-Market-1.5.0-windows-x64.zip`,
`tw-market-unified-mcp-v1.5.0-win-x64.mcpb` and their `.sha256` sidecars, plus
`TW-Market-1.5.0-first-party-sbom.json` and
`TW-Market-1.5.0-publication-manifest.json`.

## MCPB authority and resolved blockers

Owner decision: `RETAIN_MCPB_AND_ESTABLISH_REPRODUCIBLE_V1_5_BUILD_AUTHORITY`.
The immutable historical v1.0.0 bundle was re-hashed locally: 44,269,509 bytes,
6,353 members, SHA-256
`c60f2fbbfb2b4d34191d84bc5631dc7df27f39aaa7dd61c0a94f41465b7e529b`.
Its app + bundled Python dependency + manifest architecture is preserved.

The new first-party MCPB path reuses the exact Native app projection and accepted
49 Windows wheels. The A4 source was read only at its specifically authorized
wheelhouse; all filenames/hashes matched before copy, and all R1-owned copies
matched again. Missing, extra, hash mismatch and copy mismatch were all zero.
The corrected canonical wheel-lock hash is
`483bdbbffde3d7fb810931256bb2652a833749752591de38c20a9df915f3a38f`;
the aggregate inventory digest is
`d6fd4bbfa790e1e68299aaa0efa1c757392101a3c34910aef267eb7d58bed3b8`.
The prior wrong instruction digests were retracted by Owner, not repaired in Git.

MCPB manifest 0.3 retains win32, Python `>=3.13,<3.14`, Python stdio and exactly
the six current governed tool names. The official schema/license snapshot is
pinned to `anthropics/mcpb@70fe3b34cd6dff1b3bba046638edc72a6467a4fb`.
Installation uses only copied wheels with no-index/require-hashes/no-deps and no
bytecode. No network wheel resolution occurs. Current `server.json` remains the
published v1.0.0 metadata and is byte-unchanged.

Historical A/B builds differed in exactly 13 RECORD members and no other
decompressed member. Pip-generated, non-distributed launcher hashes depended on
the staging root. The canonicalizer retains all RECORD files, classifies only
exact wheel-declared non-distributed launcher rows, recomputes final payload
hashes/sizes, uses unpadded URL-safe SHA-256, sorted slash-normalized UTF-8 CSV/LF
and empty own-row hash/size. Duplicate, traversal, unresolved, malformed or
unsupported rows fail closed. Non-RECORD installed bytes are unchanged.

Fresh C/D test builds are each **40,838,005 bytes / 5,787 members**. Every
decompressed member, canonical RECORD, manifest, archive and sidecar is identical.
Test MCPB SHA-256:
`8c7a02eb93a6224ca61f3c6c46014972c1045b8d19c358e1fbe6636e3d4bad5a`.
Test sidecar SHA-256:
`732ec31fcd9f2de0cb9334843aadc28be68d32b7ee372394bc4ffbfcea996fe5`.
These are test identities only; R2 must rebuild from the eventual merged R1 source.

## Shared artifact hygiene and semantic repair

The general release validator and MCPB acceptance use the same classifier.
Current-host paths, first-party private paths/state, unsafe members and secrets
remain blocking. Each nonblocking upstream observation has exact wheel/member
byte identity and redacted match evidence. No third-party bytes were scrubbed.

The Owner's semantic adjudication separates printf/regex lexical false positives,
generic path/URI examples, approved upstream developer examples, h2py generated
source headers and Word document-authoring metadata. Classification is per match;
an additional current-host path in the same member still blocks. Exact approved
binary/text build-provenance subclasses do not create all-binary or all-text
exemptions. The shared general-validator C/D replay records these observations
per archive:

| Semantic class | Nonblocking observations |
| --- | ---: |
| Generic path/URI example | 44 |
| Upstream build provenance | 345 |
| Upstream example path literal | 5 |
| Upstream generated source provenance | 5 |
| Upstream document-authoring provenance | 7 |

FIRST_PARTY_LEAKAGE, UNPROVEN_BINARY_LEAKAGE,
UNAUTHORIZED_THIRD_PARTY_TEXT_PATH and SECRET_MATERIAL are all **0**.
Both C/D archives passed manifest conformance, exact-six checks, complete accepted
wheel-member verification, canonical RECORD verification and real packaged
launcher import via `--help` under Python network deny. This is not a full
Windows Sandbox/Local Service release acceptance.

## Validation on the implementation commit

| Gate | Result |
| --- | --- |
| Focused R1/MCPB suite | 93 passed, 0 failed, 0 skipped |
| Canonical release-blocking CI | 1895 passed, 0 failed, 4 contracted skips, 20 deselected |
| Guard | 386 events, 0 denials, 0 unexpected skips |
| Canonical member ledger | 240,240 bytes; byte-identical to A1/P0 |
| Portable validator | 205 passed, 0 failed |
| compileall scripts/server/tests | PASS |
| git diff --check | PASS |
| Source-contract dry run | schema-valid, exact implementation commit/tree |
| Final publication manifest | positive/negative synthetic proofs PASS; no final manifest claimed |

Member-ledger SHA-256 is
`1bfadc4fa5ceaaf69f1af2e3b00eec01061f931be8d487fc895f2cfe92c88418`.
External raw logs, JUnit, member ledger, guard log, dry-run source contract and
synthetic test results are bound by path/bytes/SHA-256 in the repository evidence.

The first-party SBOM was regenerated externally: **297 components**, byte-equal
to tracked authority; both SHA-256 values are
`4be21c477be71520e2bdc87b9e49d35e08dc8bea85a6654b12a3969c418913f2`.
The canonical release-note draft remains selected/unpublished and retains the
runtime, migration, OCI, signing, diagnostic-profile and historical-M6G limits.

Two external validation-harness mistakes were preserved and corrected without
tracked implementation edits: Portable runpy initially omitted its script import
directory; command logging initially collided with the source-contract output
filename. The successful Portable replay and separately named, schema-validated
dry-run instance are independently bound. The prior read-only scope incident at
the A6 evidence root is disclosed with writes/mutations/deletions all zero; that
path was not revisited in this continuation.

## Scope and remaining governance

The implementation modifies only the 21 authorized contract/packaging/test/note
paths listed and hashed in `implementation_file_inventory.json`. Existing product
runtime, dependency authority, wheel locks, VERSION, canonical A1 membership,
workflows, historical V1 manifest and accepted A1–A5/P0 evidence remain unchanged.

`STABLE_SOURCE_NOT_YET_FROZEN` and `FINAL_ARTIFACT_HASHES_NOT_YET_FROZEN`.
No final Native/Docker artifact build, Sandbox acceptance, hosted workflow,
final artifact freeze, release/tag/Registry publication or GitHub setting change
occurred. A6 overall acceptance remains NOT_YET.

- GAP-16: PARTIALLY_ADDRESSED_CONTRACT_IMPLEMENTED; final manifest not frozen.
- GAP-17: OPEN.
- GAP-18: PARTIALLY_ADDRESSED_SOURCE_CONTRACT_DEFINED.
- EXIT-16/20/21/22/23/24: NOT_YET_PASS.
- A7/stable publication/Phase M: NOT_AUTHORIZED; Phase L: NOT_CLOSED.

Next step is independent review of the exact two-commit local R1 candidate.
Only after independent acceptance and separately authorized integration does the
actual R1 merge commit/tree become an exact source candidate for R2 recertification.

Evidence: [l7-a6-r1-rc-source-contract-20261027T231400Z](acceptance_runs/l7-a6-r1-rc-source-contract-20261027T231400Z/manifest.json).
Manifest: 30 members, 0 mismatches; self-digest
`d4c29e2e446f6ebc6f67aca123339a8cd6308852018096df81cf349fe2341e7c`.
