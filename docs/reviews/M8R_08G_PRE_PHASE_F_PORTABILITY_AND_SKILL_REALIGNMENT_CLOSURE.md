# M8R-08G Pre-Phase-F portability and Skill realignment closure

Baseline: `b9cf1ca8025e8043a58912fbc91d52d80d02c31b`
Branch: `codex/m8r-08g-02-skill-portability-final-closure`

## Final-head evidence binding

The deterministic closure validation was run against local commit
`276582bf40f4cc8946e2bf74f5b682b4387fac01`, which remains available only in
the local object database.  Its comparison with final implementation candidate
`b3ea5d73268ec57f7b69df5325dbc26ac247f30a` found exactly three differences:
these two closure artifacts and `docs/roadmap/M8_POST_M8C_REVISED_ROADMAP.md`.
All three are evidence or Roadmap closure metadata; no runtime, acquisition,
qualification, Skill, schema, lockfile, or other execution-affecting file
differs.  Therefore validated code equivalence is `PASS` and the final
candidate is bound to the validation evidence.  This correction's successor
commit is evidence-only and does not repeat live acquisition.

## Decision

M8R-08G is closed.  The next authorized action is
`READY_TO_BEGIN_M8R_09_PREFLIGHT`; M8R-09 implementation has not started and
Phase F remains prohibited on this branch.

## Current authority and portable surfaces

- `docs/agent_usage_guide.md`, the current portable Skills, and canonical
  runtime/contracts are the current agent authority.  `docs/ai/` is classified
  as compatibility redirects, historical archives, or the policy-boundary
  projection; it is not a competing current authority.
- The runtime/Skill/Guide drift validator passes against the canonical and
  portable Capability Catalogs and the exact six MCP tools.
- The Security Master Skill retains its original governance coverage and now
  adds ISIN-primary instrument identity, `MARKET:CODE` listing/routing identity,
  installation-local release lifecycle, knowledge/execution separation, and
  producer-time Skill provenance.  Its validator passes 201 checks.
- The updated Security Master Skill hash is
  `e04e480a6a48a10cfe64e7334ee6233d1c866977a0666f2f1ca4fba6c1fdd62f`.
  Candidate B's historical producer hash remains
  `33be39c30a84641e7591d3d1680adb18b90efd8f509d75b3e971cb46d24c9b6d`;
  pointer and immutable historical authority bytes were not changed.

## Reproducibility and clean installation

`requirements-lock.txt` was derived in a fresh disposable CPython 3.11.15
Windows x86_64 venv after installing `requirements.txt`; pip 26.2.1 and
`pip check` passed.  The offline environment verifier checks the supported
Python version plus exact `mcp==1.29.0` and all critical imports.

A real `git clone --no-local` outside the repository was checked out at the
candidate branch head and installed from the lock in a new venv.  Schema
validation, both Skill validators, portable catalog deep equality, semantic
drift validation, compileall, and the locked environment verifier all passed.

Before initialization, `manage_security_master.py status` reported
`NOT_INITIALIZED`; a production-facing Local Service identity request returned
`409 canonical_security_master_unavailable` without a filesystem error or
traceback.  The Local Service and MCP launchers fail closed while no local
release exists.  After deterministic bootstrap, both launchers started
successfully on loopback/stdio without market retrieval.

Two independent clones had separate installation-local release roots.  A became
active while B stayed `NOT_INITIALIZED`; after B activation, A's active pointer
was unchanged.  This is installation isolation on one physical Windows host;
physical cross-machine testing was not executed.

## Bootstrap and regression evidence

The deterministic one-command update success and failure paths passed in the
fresh locked environment: success creates CANDIDATE, QUALIFIED, and an atomic
ACTIVE pointer; failure leaves the previous ACTIVE unchanged.  The portable
CLI form is compatible with the tested Python 3.11 runtime.

One and only one bounded fresh-install live bootstrap was then run.  It
succeeded with release `security-master-20260908T052023Z`, manifest hash
`eb1fc472060b8313e9de5ba5bf09933ff26daa6978b3eb1057fda48d9b2cba4d`,
46,664 records, and qualification `PASS`.  No retry loop, Candidate B fallback,
unofficial source, or bypass behavior was used.  Common shares and ETFs resolve
as execution eligible; a known warrant remains identity-resolved but execution
blocked.

Primary focused regression passed `208 passed, 1 skipped`.  The fresh-clone
default CI result was `926 passed, 9 failed, 4 skipped`; the nine failure nodes
are the exact pre-existing Mode C `artifact_hash_mismatch` lineage-fixture debt
from the baseline.  One valid local Active-release HTTP test ran and passed
instead of skipping, so the pass/skip totals differ without a new failure.

## Final state

`M8R_08G_CLOSED_READY_FOR_M8R_09_PREFLIGHT`
