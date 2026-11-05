# Documentation Index

This is the documentation front door for the **current development line**.
Choose the section that matches what you are trying to do. Historical/frozen
records remain available for audit but are not a second current-product authority.

## I want to use TW-Market

- [Operator Quick Start](operator/QUICK_START.md) — Native ZIP / MCPB / source paths
- [v1.5.1 Windows Native guided operation and RMA-0–11 improvements](operator/WINDOWS_NATIVE_V151_GUIDED_WORKFLOW.md)
- [Local Unified Workbench](operator/LOCAL_WORKBENCH.md)
- [Mode A/B/C Walkthrough](operator/MODE_ABC_WALKTHROUGH.md)
- [Troubleshooting](operator/TROUBLESHOOTING.md)
- [Changelog](../CHANGELOG.md)

## I want to use TW-Market with AI / MCP

- [Unified MCP distribution](distribution/MCP_DISTRIBUTION.md)
- [MCP Reference](reference/MCP_REFERENCE.md)
- [AI discovery entry (`llms.txt`)](../llms.txt)
- [Current AI usage guide](agent_usage_guide.md)
- [Portable TW-Market Agent Skill](../skills/tw-market-evidence-agent/SKILL.md)
- [Capability Matrix](reference/CAPABILITY_MATRIX.md)
- [Current V3 capability catalog](data_capabilities/unified_market_evidence_capability_catalog.v3.json)
- [Current V3 routing matrix](data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json)

## I want to understand the architecture

- [Architecture README](architecture/README.md)
- [Product Architecture](architecture/PRODUCT_ARCHITECTURE.md)
- [Data Flow](architecture/DATA_FLOW.md)
- [Source and Capability Model](architecture/SOURCE_AND_CAPABILITY_MODEL.md)
- [Output Artifacts](reference/OUTPUT_ARTIFACTS.md)
- [Governance Boundaries](reference/GOVERNANCE_BOUNDARIES.md)

## I want to develop or contribute

- [PROJECT.md](../PROJECT.md) — current project/product authority
- [HANDOFF.md](../HANDOFF.md) — current operational stopping point
- [ROADMAP.md](../ROADMAP.md) — canonical Roadmap V3.2
- [AGENTS.md](../AGENTS.md) — repository and AI collaboration rules
- [Contributing](../CONTRIBUTING.md)

## I want to audit governance or release provenance

- [Governance Index](governance/INDEX.md)
- [Project History](PROJECT_HISTORY.md)
- [Release docs](release/README.md)
- [Published v1.5.1 stable / six-asset SHA-256](release/V1_5_1_RELEASE_PUBLICATION.md)
- [CURRENT GitHub platform protection and signing governance](release/GITHUB_PLATFORM_AND_SIGNING_GOVERNANCE.md)
- [V1.0.0 stable release snapshot](release/V1_RELEASE.md)
- [Phase L governance](governance/phase_l/)
- [Acceptance runs](acceptance_runs/)
- [Acceptance records](acceptance/)
- [Reviews](reviews/)
- [Protocols](protocol/)
- [Archive](archive/README.md)

Current Stable is [`v1.5.1`](release/V1_5_1_RELEASE_PUBLICATION.md); its frozen
source is commit `1f3666eefdca7e2e9a1c88099f802696bf7970d6`, tree
`d67e9bc1db34ff268b5b8d0f2a301d1a211df3b6`. Previous `v1.5.0` remains
a separate historical release. Documentation-only commits on `main` do not
redefine any already published tag/source/assets.

## Engineering history / protocol archive

The audit links above include historical reviews, protocols, acceptance runs, and
archived frontdoors. They are retained as evidence/history and do not form a
second current-product authority.

## Historical-document rule

Statements such as `NOT_AUTHORIZED`, `unpublished`, an older preferred contract,
or an older stop point may be correct inside a frozen/historical record. Do not
mass-edit accepted ledgers to current wording. Fix current contradictions only in
current frontdoor documents.

Phase M remains **NOT_AUTHORIZED**. Live network acceptance is always separately
bounded and explicitly authorized; ordinary documentation/development work does
not grant network or monitoring authority.
