# TW-Market GitHub Platform Protection & Publisher Provenance (CURRENT)

**Checkpoint:** 2026-11-05 · Owner-authorized GitHub platform-governance work

This CURRENT governance record applies to the public repository
[SmartyJohnway/tw-market-live-data-intelligence](https://github.com/SmartyJohnway/tw-market-live-data-intelligence).
It does **not** modify an existing published release or replace frozen
L7 source, Manifest or acceptance evidence.

## Active GitHub protections (API readback verified)

| Surface | Control | Enforced result |
|---|---|---|
| Default branch `main` | Ruleset **26585025**, main baseline | Active; deny deletion and non-fast-forward/force pushes, no bypass |
| Published `v1.5.1` tag | Ruleset **26585038**, frozen tag | Active; deny update and deletion of exact Tag, no bypass |
| Future GitHub Releases | Repository **Immutable Releases** | `enabled=true`, `enforced_by_owner=false` (repository-level setting) |
| Existing `v1.5.1` Release | ID `434114288` | `immutable=false`; not retroactively immutable |

Normal fast-forward changes to `main` are **not** blocked by the minimal
branch ruleset. **Pull request reviews and required hosted status checks
are NOT enforced.** Most current workflows are manually triggered; do
not require an absent/untested CI status that could prevent updates.
A stronger PR+CI merge policy needs a separately authorized, validated
automatic check.

Ruleset administration pages:

- [Main ruleset](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/rules/26585025)
- [Frozen v1.5.1 Tag ruleset](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/rules/26585038)

## Three separate kinds of trust

**1. Integrity (SHA-256, Tag, Manifest binding).** The published
[v1.5.1 Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1)
has six verified asset digests. Its annotated Git Tag object is
`6f7d207ba7f58b82a76f309d7d301f200b2f34eb`, targeting
source commit `1f3666eefdca7e2e9a1c88099f802696bf7970d6`.
The Publication Manifest SHA-256 is
`791b42375f4f9d747d4389fcd0113dab16367aa04d6bd6b8bc8b95598be7af2b`.
These prove byte identity and source binding, **not a cryptographic
publisher signature**.

**2. GitHub-managed attestations on FUTURE immutable releases.** GitHub's
Immutable Releases are now enabled. When a later release is published
under this policy, GitHub supplies signed Sigstore Release attestations.
The setting by itself is not evidence that a future release has been
published or that a particular local file has passed verification.
The signer identity is GitHub's release provenance mechanism, not a
personal manufacturer's code-signing certificate.

For a **later actually published** immutable release, validate with a
current GitHub CLI and a local copy of the artifact:

~~~powershell
gh release verify vNEXT --repo SmartyJohnway/tw-market-live-data-intelligence
gh release verify-asset vNEXT C:\path\to\exact-downloaded-artifact.zip --repo SmartyJohnway/tw-market-live-data-intelligence
Get-FileHash C:\path\to\exact-downloaded-artifact.zip -Algorithm SHA256
~~~

`vNEXT` and the path are placeholders. Before acceptance, both Release
attestation and asset attestation verification must pass; compare the
downloaded asset digest with the new release's Manifest separately.

**3. Personal publisher signature / Authenticode / signed commits.**
These are **distinct** from the GitHub-managed release attestations.
No personal GPG/Cosign signer, Authenticode code-signing certificate,
or signed Git commit/tag policy is established by this checkpoint.
Their status remains **NOT_ESTABLISHED** pending a separate signer
identity/key-custody decision and independently verified signing.
Never commit private keys, passphrases, tokens or certificate material
to this public repository or its Release artifacts.

## The existing v1.5.1 exception

GitHub's policy is **future Releases only**. Thus the existing `v1.5.1`
still reports `immutable=false` even though a separate active Tag
ruleset now forbids Tag update/deletion. A read-only
`gh release verify v1.5.1` on 2026-11-05 returned
`no attestations for tag v1.5.1`. This is a truthful pre-policy
condition; **do not rewrite/re-publish the Tag or six assets** merely
to obtain retroactive attestation claims.

Status:
- `v1.5.1`: **STABLE_PUBLISHED / HASH_VERIFIED / TAG_REF_PROTECTED**.
- `v1.5.1`: **RELEASE_IMMUTABLE=false / SIGNED_ATTESTATION=NOT_ESTABLISHED**.
- Future Releases: **IMMUTABILITY=ENABLED**, with signed release
  attestation **NOT_YET_EXECUTED/VERIFIED** until a new one is published.

## Gate for any next official release

1. Separate explicit Owner release authorization and exact source,
   acceptance, CI, dependency, Tag/Manifest and distribution bindings.
2. Stage Draft assets and preflight the complete exact candidate,
   including ZIP/MCPB bytes, six assets, hashes and Manifest.
3. Publish once only when all assets are final. For later immutable
   Releases, GitHub locks Release assets and Tag after publication;
   corrections require a new version, not in-place replacement.
4. Require the actual published Release API `immutable=true`,
   successful `gh release verify` and `gh release verify-asset`,
   and separately checked SHA-256 of downloaded artifacts.
5. Save the actual signer/attestation verification, Release ID,
   Tag, source commit/tree, asset hashes and reviewer-owned result.
   **No evidence, no PASS.**
6. Never label GPG, Authenticode or independent publisher identity
   signing as complete unless cryptographically performed and verified.

## Operations and future stronger protection

- Authorized ordinary fast-forward development is still permitted.
  Force pushes and branch deletion are blocked on `main`; updates/
  deletions of the frozen `v1.5.1` Tag are blocked by exact ruleset.
- Ruleset emergency disable/update requires separate explicit Owner
  authorization, a pre-change snapshot, recorded reason, and post-change
  readback. Do not bypass silently.
- Adding PR reviews and required hosted CI must follow a tested
  automatic workflow; do **not** require a non-existent status today.
- Registry publication remains historical `1.0.0` and separate from
  GitHub `v1.5.1`; Docker validation-only and Phase M remain separate.
  Native Runtime, source and historical evidence are not changed here.

**No evidence, no PASS.**
