# TW-Market Release Documentation (CURRENT index)

The **latest published GitHub Stable is `v1.5.1`**, frozen at
`1f3666eefdca7e2e9a1c88099f802696bf7970d6`
(2026-11-04). Start with:

- [v1.5.1 — Published Release, all six asset SHA-256](V1_5_1_RELEASE_PUBLICATION.md)
- [GitHub v1.5.1 Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1)
- [Operator Native/MCPB Quick Start](../operator/QUICK_START.md)
- [Unified MCP Distribution](../distribution/MCP_DISTRIBUTION.md)
- [Current Changelog](../../CHANGELOG.md)

## Current release governance versus historical milestones

The current v1.5.1 Readiness used the accepted `release-blocking-ci` gate,
a separate Release Readiness profile, Native/MCPB offline acceptance,
Docker validation-only acceptance, source/artifact binding and independent
publication-manifest review. Supplemental `default-ci` and
`full_non_network` FAIL were retained, not promoted to PASS.

The following files remain available as **historical acceptance/instructions
for their original versions**, not current v1.5.1 publication status:

- [V1.0.0 stable source snapshot](V1_RELEASE.md)
- [V1.0 historical migration](V1_MIGRATION.md)
- [V1.0 historical release candidate](V1_RELEASE_CANDIDATE.md)
- [V1.0 release notes draft](V1_0_RELEASE_NOTES_DRAFT.md)
- [v1.5.0 prepublication draft](V1_5_0_RELEASE_NOTES_DRAFT.md)
- [v1.5.1 source-bound **prepublication draft**](V1_5_1_RELEASE_NOTES_DRAFT.md)
- [A1 historical release checklist](RELEASE_CHECKLIST.md)
- [Historical M5 release candidate](M5_LOCAL_RELEASE_CANDIDATE.md)
- [Legacy M5 release readiness](../RELEASE_READINESS.md)
- [Legacy M5 release checklist](../release_checklist.md)

**Do not edit the source-bound v1.5.1 Draft** to make its dated
prepublication text appear current: it is byte-bound to the published
Publication Manifest. The new publication page is the current release record.
MCP Registry `1.0.0` and Docker local build remain separate publication
surfaces; Phase M stays `NOT_AUTHORIZED`.
