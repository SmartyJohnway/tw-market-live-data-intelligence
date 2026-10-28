# Post-Phase-L F5-R1 — Independent-Review Corrections

Date: 2026-10-28

Status: **CANDIDATE_COMPLETE / CORRECTION_GATE_PASS**

## Purpose

F5-R1 corrects only the three documentation findings from the cumulative
F0-F5 independent review. It does not change runtime behavior, frozen release
artifacts, MCP Registry metadata, Docker publication state, or Phase M authority.

Frozen v1.5.0 release identity remains:

- commit: `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`
- tree: `d44f66dc154c21326ac8b105d2f15fd793f6071b`
- GitHub release: `v1.5.0`

## Corrections

- **IR-001 CLOSED:** current docs now distinguish governance-frozen / SHA-256-
  verified release authority from GitHub platform immutability. GitHub live API
  still reports `immutable=false` for v1.5.0.
- **IR-002 CLOSED:** six ASCII `?` substitutions in `AGENTS.md` were restored to
  the intended em/en-dash punctuation (`—` / `–`).
- **IR-003 CLOSED:** both READMEs now expose a thin Native ZIP / MCPB / source
  `Choose your path` entry plus an explicit 60-second Quick Start pointer.
## Validation

Targeted finding checks:

- release immutability overclaim scan: PASS / zero hits;
- `AGENTS.md` ASCII punctuation corruption scan: PASS / zero hits;
- bilingual three-path onboarding: PASS;
- bilingual 60-second Quick Start pointer: PASS;
- GitHub live `v1.5.0` field: `immutable=false` confirmed;
- `git diff --check`: PASS.

Current validators all PASS. Current local Markdown links resolve **117 / 117**.
A fresh workspace-local pytest base reran the same independent-review focused
suite with **141 passed / 0 failed**.

## Boundary

F5-R1 does not authorize commit, push, PR, merge, Registry publication, Docker
publication, release mutation, or Phase M. The corrected cumulative candidate is
ready for a new independent re-review; the prior BLOCKED decision is not treated
as automatically superseded until that re-review accepts the corrected diff.
