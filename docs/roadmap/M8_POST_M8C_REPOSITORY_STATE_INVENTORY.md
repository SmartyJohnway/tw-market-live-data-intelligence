# M8 Post-M8C Repository State Inventory

Baseline SHA: `bd3496efe7492e6cd3c7dacc169e142f90e6cd92`. Remote baseline: `origin/main` at the same SHA.

## Scope inspected

Inspected `README.md`, `docs/`, `docs/protocol/`, `docs/contracts/`, `docs/contracts/schemas/`, `docs/data_capabilities/`, `scripts/`, `server/`, `skills/`, `tests/`, `.github/workflows/`, requirements and configuration manifests. No live network validation was executed by this audit.

## Implemented capability inventory

The repository contains governed source registries, official EOD adapters, TAIFEX OpenAPI adapters, TAIFEX MIS bounded runtime helpers, M8R bounded request/orchestration contracts, M8R-03C watchlist bundle builders, M8R-03D controlled execution planning/results, M8R-03D-F1 security-master snapshot adapter, and M8R-03E AI-context handoff builders and validators.

## Track-by-track status matrix

| Track | Status | Registry/docs evidence | Runtime/CLI evidence | Test evidence | Known caveats | Declared successor | Actual successor |
|---|---|---|---|---|---|---|---|
| M8-00 | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8A | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8B | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8C | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-01 | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-01F | completed | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-02A | implemented_not_live_validated | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-02B | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-02B-F1/F2 | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-03B | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-03C | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-03D | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-03D-F1 | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| M8R-03E | completed_with_caveats | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | M8R-05A-UNIFIED-MARKET-EVIDENCE-CONTRACT-AND-CAPABILITY-CATALOG |
| original M8R-04 | superseded | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| historical M8E | historical_only | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |
| historical M8F | historical_only | protocol and registry artifacts inspected | scripts/tests present where applicable | unit fixtures present; live validation only where historical artifacts record it | fixture-vs-live and manual execution caveats remain | varies by historical artifact | post-R1 roadmap Phase B or R2 only if blockers appear |

## Source/runtime status

TWSE_MIS and TAIFEX_MIS are accepted as controlled runtime observation families with caveats; TWSE_OpenAPI, TPEx_OpenAPI, and TAIFEX_OpenAPI are official reference/EOD/statistical context families. Yahoo/FinMind remain optional validation or historical context unless explicitly upgraded.

## Contract and testing status

Contracts and schemas exist for M8R-03B/C/D/E flows. Tests distinguish many fixture and CLI paths, but cross-layer producer/consumer compatibility, large input behavior, duplicate JSON key handling, and path/symlink safety remain remediation backlog items.

## Evidence references

Primary evidence includes `docs/data_capabilities/m8_source_capability_registry.json`, `docs/protocol/M8R_03E_WATCHLIST_AI_CONTEXT_PACKAGE_AND_CONVERSATION_HANDOFF.md`, M8R unit tests under `tests/unit/test_m8r_*.py`, and runtime helpers under `scripts/m8r_*.py`.
