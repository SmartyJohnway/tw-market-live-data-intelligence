# Documentation Index

This index is the product documentation entry point after M5LRM architecture convergence. Historical milestone reports remain under `docs/reviews/`; product-oriented references live in the sections below.

## Architecture

- [Architecture Overview](architecture/architecture_overview.md)
- [Level 1 Canonical Context](architecture/level1_canonical.md)
- [Level 2 Live Observation](architecture/level2_live_observation.md)
- [Mode A / Mode B / Mode C](architecture/mode_abc.md)
- [AI Watchlist Workflow and Conversation Context](architecture/ai_watchlist_workflow.md)
- [Source Adapter Architecture](architecture/source_adapter_architecture.md)
- [Local-First Market Context Architecture](architecture/LOCAL_FIRST_MARKET_CONTEXT_ARCHITECTURE.md)

## Protocol and Contracts

- [Data Contract](data_contract.md)
- [M2 Source Contract Baseline](protocol/M2_SOURCE_CONTRACT_BASELINE.md)
- [M2 Normalized Schema Inventory](protocol/M2_NORMALIZED_SCHEMA_INVENTORY.md)
- [TWSE MIS Protocol](protocol/TWSE_MIS_PROTOCOL.md)
- [TAI/TW source target support matrix](protocol/SOURCE_TARGET_SUPPORT_MATRIX.md)
- [Watchlist Observation Semantics](protocol/WATCHLIST_OBSERVATION_SEMANTICS.md)
- [M3G Controlled Live Probe Output Contract](protocol/M3G_CONTROLLED_LIVE_PROBE_OUTPUT_CONTRACT.md)
- [M5C Staging Promotion Contract](protocol/M5C_STAGING_PROMOTION_CONTRACT.md)
- [M5D Frontend Publication Contract](protocol/M5D_FRONTEND_PUBLICATION_CONTRACT.md)

## Validation

- [Test Suite Segmentation](testing/TEST_SUITE_SEGMENTATION.md)
- [Release Readiness](RELEASE_READINESS.md)
- [M5L Live Sources Validation Matrix](m5l_live_sources_validation_matrix.md)
- [M5L TAIFEX Live Source Validation](m5l_taifex_live_source_validation.md)

## Operations

- [Operations Runbook](operations_runbook.md)
- [AI Watchlist Operator Guide](operator/AI_WATCHLIST_OPERATOR_GUIDE.md)
- [M5OP Operator Workflow](operator/M5OP_OPERATOR_WORKFLOW.md)
- [MCP Usage Guide](mcp_usage_guide.md)
- [Agent Usage Guide](agent_usage_guide.md)
- [Source Authority Manual](manuals/SOURCE_AUTHORITY_MANUAL.md)
- [Operator Staging Workflow Manual](manuals/OPERATOR_STAGING_WORKFLOW_MANUAL.md)
- [Frontend Caveat Display Manual](manuals/FRONTEND_CAVEAT_DISPLAY_MANUAL.md)
- [Troubleshooting Guide](manuals/TROUBLESHOOTING_GUIDE.md)

## Governance and Source Registry

- [Governance Index](governance/INDEX.md)
- [Source Failure Playbook](source_failure_playbook.md)
- [Recommended Architecture](recommended_architecture.md)
- [Capability Matrix](capability_matrix.md)

## Archive and Reviews

- [Archived pre-M5LRM README](archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md)
- [Reviews directory](reviews/)
- [Release directory](release/)

## Safe local validation commands

```bash
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
python scripts/run_m5k_postmerge_validation.py --check-only
python scripts/governance_forbidden_path_guard.py
python scripts/forbidden_behavior_scanner.py
git diff --check
```

Boundaries remain: no live probes by default, no production refresh, no `frontend/public` writes, no `research/generated` writes, no `production/prod` writes, no broker/auth credentials, no trading signals, and no realtime guarantee.
