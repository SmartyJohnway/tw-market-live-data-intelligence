# Documentation Index

This page is the documentation front door for the **current development line**.
Historical milestone documents remain available for audit, but they are not a
second current-product authority.

## Repository governance — start here

1. [PROJECT.md](../PROJECT.md) — current product/project truth
2. [ROADMAP.md](../ROADMAP.md) — canonical Roadmap V3.2
3. [HANDOFF.md](../HANDOFF.md) — current operational stopping point
4. [AGENTS.md](../AGENTS.md) — repository and AI collaboration rules

## Current product docs

### Operator

- [Operator Quick Start](operator/QUICK_START.md)
- [Local Unified Workbench](operator/LOCAL_WORKBENCH.md)
- [Mode A/B/C Walkthrough](operator/MODE_ABC_WALKTHROUGH.md)
- [Troubleshooting](operator/TROUBLESHOOTING.md)

### Architecture

- [Architecture README](architecture/README.md)
- [Product Architecture](architecture/PRODUCT_ARCHITECTURE.md)
- [Data Flow](architecture/DATA_FLOW.md)
- [Source and Capability Model](architecture/SOURCE_AND_CAPABILITY_MODEL.md)

### Reference

- [Capability Matrix](reference/CAPABILITY_MATRIX.md)
- [Source Matrix](reference/SOURCE_MATRIX.md)
- [MCP Reference](reference/MCP_REFERENCE.md)
- [Output Artifacts](reference/OUTPUT_ARTIFACTS.md)
- [Governance Boundaries](reference/GOVERNANCE_BOUNDARIES.md)

### AI / Agent

- [Current AI usage guide](agent_usage_guide.md)
- [Portable TW-Market Agent Skill](../skills/tw-market-evidence-agent/SKILL.md)
- [Current V3 capability catalog](data_capabilities/unified_market_evidence_capability_catalog.v3.json)
- [Current V3 routing matrix](data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json)

### Governance / acceptance

- [Governance Index](governance/INDEX.md)
- [Phase H governance](governance/phase_h/)
- [Acceptance runs](acceptance_runs/)
- [Acceptance records](acceptance/)

### Release / distribution

- [Release docs](release/README.md)
- [V1.0.0 stable release snapshot](release/V1_RELEASE.md)
- [MCP distribution](distribution/MCP_DISTRIBUTION.md)

## Engineering history / protocol archive

The following directories are evidence/history-heavy. Statements such as
"next task", "V2 preferred", "Phase G not started", or an older release status
may be correct **for the milestone when the document was created** and must not
be interpreted as current state without checking the root governance files.

- [Project History](PROJECT_HISTORY.md)
- [M8 through M8B consolidated final acceptance](protocol/M8_THROUGH_M8B_CONSOLIDATED_FINAL_ACCEPTANCE.md) — historical milestone evidence, not current runtime authority
- [Reviews](reviews/)
- [Protocols](protocol/)
- [Historical acceptance runs](acceptance_runs/)
- [Roadmap history](roadmap/)
- [Archive](archive/README.md)

Do not mass-edit historical ledgers or closure reports to match later runtime
state. Current contradictions should be fixed in current entry-point docs.

## Current deterministic validation

```bash
python -m compileall -q scripts server tests
python scripts/validate_phase_h_v3_contracts.py
python scripts/validate_portable_catalog_sync.py
python scripts/validate_runtime_skill_guide_sync.py
python scripts/run_test_profile.py default-ci
git diff --check
```

Live network acceptance is separately authorized and bounded.
