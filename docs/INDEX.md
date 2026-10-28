# Documentation Index

This is the documentation front door for the **current development line**.
Choose the section that matches what you are trying to do. Historical/frozen
records remain available for audit but are not a second current-product authority.

## I want to use TW-Market

- [Operator Quick Start](operator/QUICK_START.md) — Native ZIP / MCPB / source paths
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
- [V1.0.0 stable release snapshot](release/V1_RELEASE.md)
- [Phase L governance](governance/phase_l/)
- [Acceptance runs](acceptance_runs/)
- [Acceptance records](acceptance/)
- [Reviews](reviews/)
- [Protocols](protocol/)
- [Archive](archive/README.md)

Current stable product is `v1.5.0`; its frozen source is commit
`acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`, tree
`d44f66dc154c21326ac8b105d2f15fd793f6071b`. Later documentation commits on
`main` do not redefine that release.

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
