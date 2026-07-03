# Documentation Index

Master map for the M5 Local Release Candidate. Links below point to current product docs unless explicitly marked archive or historical review.

## Start here

- [Repository README](../README.md)
- [Operator Quick Start](operator/QUICK_START.md)
- [Mode A/B/C Walkthrough](operator/MODE_ABC_WALKTHROUGH.md)
- [M5 Local Release Candidate](release/M5_LOCAL_RELEASE_CANDIDATE.md)
- [Project History](PROJECT_HISTORY.md)

## Architecture

- [Architecture README](architecture/README.md)
- [Product Architecture](architecture/PRODUCT_ARCHITECTURE.md)
- [Mode A/B/C and Level 1/2](architecture/MODE_ABC_LEVEL12.md)
- [Data Flow](architecture/DATA_FLOW.md)
- [Source and Capability Model](architecture/SOURCE_AND_CAPABILITY_MODEL.md)

## Operator guides

- [Operator README](operator/README.md)
- [Quick Start](operator/QUICK_START.md)
- [Mode A/B/C Walkthrough](operator/MODE_ABC_WALKTHROUGH.md)
- [Conversation Package Guide](operator/CONVERSATION_PACKAGE_GUIDE.md)
- [Source Health Guide](operator/SOURCE_HEALTH_GUIDE.md)
- [Troubleshooting](operator/TROUBLESHOOTING.md)

## Reference

- [Reference README](reference/README.md)
- [Source Matrix](reference/SOURCE_MATRIX.md)
- [Capability Matrix](reference/CAPABILITY_MATRIX.md)
- [API Reference](reference/API_REFERENCE.md)
- [MCP Reference](reference/MCP_REFERENCE.md)
- [Output Artifacts](reference/OUTPUT_ARTIFACTS.md)
- [Governance Boundaries](reference/GOVERNANCE_BOUNDARIES.md)

## Contributor docs

- [Contributor README](contributor/README.md)
- [Contributing](contributor/CONTRIBUTING.md)
- [Development Guide](contributor/DEVELOPMENT_GUIDE.md)
- [Testing Guide](contributor/TESTING_GUIDE.md)
- [Documentation Guide](contributor/DOCUMENTATION_GUIDE.md)

## Release docs

- [Release README](release/README.md)
- [Release Checklist](release/RELEASE_CHECKLIST.md)
- [M5 Local Release Candidate](release/M5_LOCAL_RELEASE_CANDIDATE.md)
- [M5R Documentation Audit](release/M5R_DOCUMENTATION_AUDIT.md)

## Reviews / acceptance

- [Reviews README](reviews/README.md)
- [M5XR Final Mode ABC Level 1/2 Release Acceptance](reviews/M5XR_FINAL_MODE_ABC_LEVEL12_RELEASE_ACCEPTANCE.md)
- [M6A Observation UX and Local Frontend Compatibility](reviews/M6A_OBSERVATION_UX_AND_LOCAL_FRONTEND_COMPATIBILITY.md)

## Archive

- [Archive README](archive/README.md)
- [Archived pre-M5R README](archive/readme/README_PRE_M5R_20260630_PRODUCT_RELEASE_HARDENING.md)
- [Archived pre-M5LRM README](archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md)

## Core validation commands

```bash
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
python scripts/run_m5k_postmerge_validation.py --check-only
python scripts/run_m5q_source_health_probe.py --check-only
python scripts/build_m5n_conversation_context.py
python scripts/governance_forbidden_path_guard.py
python scripts/forbidden_behavior_scanner.py
git diff --check
```
