# M8R-06-01 Implementation Acceptance

**Milestone**: M8R-06-01
**Task**: M8R-06-01-UNIFIED-WORKBENCH-MODE-A-INSPECT-AND-VALIDATE
**Status**: BLOCKED
**Principal Decision**: M8R-06-01_BLOCKED_BY_CANONICAL_SECURITY_MASTER_CONFIGURATION
**Next Task**: M8R-06-02_NOT_AUTHORIZED

## Overview
Mode A of the Unified Operator Workbench has been implemented, establishing an offline, deterministic boundary for inspecting and validating unified market evidence requests against the F3 canonical runtime. However, production activation is **BLOCKED** because the required canonical security master snapshot configuration does not exist in the repository.

## Required Acceptance Gates
- **Gate A (Canonical F3 reuse)**: PASS. Reused `validate_unified_market_evidence_request` without duplicating logic.
- **Gate B (Complete canonical result)**: PASS in code design, but production unreachable due to missing canonical security master.
- **Gate C (Offline guarantee)**: PASS_WITH_REQUIREMENTS. Asserted via monkeypatched `socket`, `httpx` unit tests and CSP headers in HTML.
- **Gate D (Localhost boundary)**: PASS. `scripts/run_unified_workbench.py` strictly binds Uvicorn to 127.0.0.1.
- **Gate E (No Mode B leakage)**: PASS. No preview or authorization endpoints are present. The UI button for Mode B is permanently disabled in Mode A.
- **Gate F (Resource containment)**: PASS. Canonical schemas and capability catalogs are resolved via internal absolute paths. User input of arbitrary file paths is prohibited.
- **Gate G (UI state discipline)**: PARTIAL. Validation result states enforce boundaries, but the initial production state fails closed.
- **Gate H (Error separation)**: PASS. API transport errors return HTTP statuses (400, 413, 422, 500) while F3 domain validation issues return 200 with `blocking_issues`.
- **Gate I (Security)**: PASS_WITH_CAVEATS. Body limited to 1MiB, HTML CSP set to self, arbitrary paths blocked, and production fixture fallback is disabled.
- **Gate J (Tests)**: NOT_PROVEN. M5D/M5E tests passing, but Mode A production tests fail closed due to missing configuration.

## Blocking Findings
- `canonical_security_master_unavailable`: The production `config/production_security_master_snapshot.json` and its manifest are missing, causing the system to fail closed in production usage and during the `--startup-check`.
