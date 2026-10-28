# L7 RC source and publication manifest contract

Status: R1 source contract candidate; independent review pending.

The committed schemas and builders are machinery. An RC source-contract instance
is generated externally against a clean, immutable Git commit/tree. It binds
tracked HEAD bytes, VERSION 1.5.0, artifact-set policy, dependency locks, runtime
policy and the deterministic first-party SBOM. It contains no final artifact
hashes. No instance is committed into the commit whose hash it describes.

The later final publication manifest consumes explicit schema-validated source,
artifact and validation bindings plus the source-bound release-note file. Every
binding must agree on source commit/tree and product version. Supplied assets are
read explicitly; their sizes and SHA-256 are recomputed. Missing, undeclared,
duplicate, mismatched or placeholder inputs fail closed. There is no moving
artifact discovery or current-time field in content identity.

`MANIFEST_SELF_HASH_EXTERNAL_BINDING`: the manifest does not include its own
SHA-256. A6 evidence binds its final bytes externally; A7 later verifies the
uploaded asset digest. This prevents a manifest/sidecar/self-hash cycle. Native
and MCPB sidecars each describe only their corresponding archive.

## Canonical artifact-set policy

`config/l7_release_artifact_set.v1.json` declares publication assets: Native
`TW-Market-1.5.0-windows-x64.zip` and `.sha256`, Windows MCPB
`tw-market-unified-mcp-v1.5.0-win-x64.mcpb` and `.sha256`, first-party SBOM
`TW-Market-1.5.0-first-party-sbom.json`, and the additive L7 publication manifest.

The MCPB retention decision is `RETAIN_MCPB_AND_ESTABLISH_REPRODUCIBLE_V1_5_BUILD_AUTHORITY`.
Its Python 3.13 / Windows stdio model uses the same exact six governed tools,
the existing Native app projection, exact accepted 49 Windows wheels, offline
hashed pip, canonical installed RECORD metadata and deterministic ZIP bytes.
R1 test archive hashes are not final publication hashes. Current published
v1.0.0 Registry metadata remains unchanged; A7 owns eventual updates.

Docker is VALIDATION_ONLY with `registry_publication = false`. The typed
validation binding records base digest, image identity, RootFS/content hashes,
source identity and runtime configuration under
`REPRODUCIBLE_ROOTFS_CONTENT_WITH_EXPLICIT_OCI_METADATA_BOUNDARY`. It makes no
byte-identical OCI image claim.

GitHub-generated source ZIP/tarball are PLATFORM_GENERATED; final tag/source
identity is authoritative. Prepublication project-generated hashes are not
required for those archives. Historical v1.0.0 MCPB/sidecar and V1 manifest remain
HISTORICAL_ONLY; they cannot silently become v1.5 publication assets. The
historical V1 schema/builder remain unchanged for readiness smoke.

## SBOM, signing and hygiene

The release SBOM is a byte-derived copy of accepted
`config/first_party_dependency_sbom.json`, externally regenerated using
`scripts.dependency_authority` and compared byte-for-byte. It is lightweight
first-party JSON, not a new SPDX/CycloneDX conversion. Its accepted scope text
remains historical input provenance; final publication source/artifact binding
is supplied by the additive L7 manifest.

Hashes, provenance and SBOM are not cryptographic publisher signatures.
Publisher signing-key/certificate authority is NOT_ESTABLISHED. No key creation
or signing workflow is introduced.

`validate_l7_release_artifact_hygiene.py` and MCPB share
`packaging_mcpb.hygiene`. Unsafe ZIP names, symlinks, first-party private machine
paths/state, credential members and secret material block. Scanning never
extracts arbitrary ZIP names or reports secret contents. Each nonblocking
third-party observation requires exact accepted wheel/member hashes and byte
identity, redacted match evidence, non-current-host and non-secret proof.

Semantic classifications distinguish lexical false positives, generic examples,
reviewed upstream demo literals, h2py generated-source headers and Word template
authoring metadata from private-machine leakage. Classification is per match;
another actual private path in the same member still blocks. Binary build
provenance and the Owner-authorized NumPy/cryptography/exact DELVEWHEEL/SBOM text
subclasses are narrow; there is no all-binary or all-text exemption. Unresolved
matches fail closed. Accepted third-party bytes are never scrubbed or patched;
only installed `.dist-info/RECORD` is regenerated from final payload bytes.

## Later responsibilities

`STABLE_SOURCE_NOT_YET_FROZEN`: the R1 feature HEAD cannot predeclare its eventual
merge commit. After independent acceptance and normal merge, the actual R1 merge
commit/tree becomes the source candidate for R2. R2 freshly recertifies CI,
Native/Windows 11, MCPB, Docker, hygiene and SBOM export from that exact source.

`FINAL_ARTIFACT_HASHES_NOT_YET_FROZEN`: R3 later freezes the final publication
manifest, source/artifact identities, release notes and gap/exit adjudication,
including the branch/check/protection decision. A7 separately owns publication,
asset upload, Registry update and post-publication verification.

R1 does not pass EXIT-16/20/21/22/23/24. A7/stable publication/Phase M remain
NOT_AUTHORIZED and Phase L remains NOT_CLOSED.
