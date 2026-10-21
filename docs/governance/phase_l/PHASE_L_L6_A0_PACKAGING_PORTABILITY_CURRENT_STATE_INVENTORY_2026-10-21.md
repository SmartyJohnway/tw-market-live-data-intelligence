# Phase L6-A0 — Packaging & Portability Current-State Inventory

**Technical disposition: `L6_A0_PACKAGING_PORTABILITY_INVENTORY_COMPLETE`**

**Phase L5:** CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`  
**Phase L6:** STARTED  
**L6-A0:** TECHNICAL INVENTORY COMPLETE / OWNER ACCEPTANCE PENDING  
**L6-A1+:** NOT AUTHORIZED  
**Docker implementation:** NOT AUTHORIZED  
**Installer implementation:** NOT AUTHORIZED  
**L7:** NOT AUTHORIZED  
**Phase M:** NOT AUTHORIZED

Owner authorities:

- `USER_CHAT_2026-10-21_PHASE_L_L6_A0_PACKAGING_PORTABILITY_INVENTORY_AUTHORIZATION`
- `USER_CHAT_2026-10-21_WINDOWS11_NATIVE_TIER1_BASELINE_SUPERSESSION`

## Exact entry and closure provenance

Inventory was based on canonical `origin/main` `c546232ed24fdb781a605e4403961d7ffb16a339`, tree `689fb647e5401a75ee4b89fcf36710fc27324aee`, in isolated branch `phase-l/l6-a0-packaging-portability-inventory`. This base contains A7 Owner final closure: PR #395 merged at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`; the accepted closure record is `PHASE_L_L5_OWNER_FINAL_CLOSURE_2026-10-21.md`. The original checkout and its untracked `data/` were not used or modified.

Frozen architecture authority remains `PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`. L0-D03 remains byte-for-byte historical: it records Windows 10 x64 and Windows 11 x64 as Tier-1. The prospective Owner policy supersedes that baseline only for L6 onward: Native Tier-1 is Windows 11 x64 only; Windows 10 is not release-blocking. See `PHASE_L_L6_WINDOWS11_TIER1_PROSPECTIVE_POLICY_SUPERSESSION_2026-10-21.md`.

## Findings

The replaceable application is currently a source checkout. Product entrypoints, Python imports, schemas, Catalog/Route, executor metadata, frontend files, skills, classifier resources, requirements, and version lookup are resolved relative to repository paths. The current lifecycle (`python -m scripts.tw_market {init,start,status,stop,doctor}`) has no `init` command yet; `start/status/stop/doctor` are present. The other active entrypoint groups are the Local Workbench launcher, stdio MCP launcher, and explicit Security Master manager.

There is no single persisted user-configuration authority. Current production roots are selected through process environment and repository-local defaults; Security Master management also accepts an explicit `--root`. The frozen precedence includes a user-config layer that is not implemented. Current roots are therefore checkout-, environment-, or caller-path-dependent.

The candidate responsibility for a future `init` is limited to installation identity, selecting/verifying physical state roots, persisted user configuration, directory creation/verification, an installation/state version marker, and writable-root validation. It must not acquire, refresh, build, qualify, or activate Security Master data. `manage_security_master.py update --live` remains a separate explicit operation. `start` must continue to accept `NOT_INITIALIZED`; `doctor` remains read-only. This is derived candidate scope, not an implementation or a newly frozen command contract.

The strongest concrete packaging blocker is Security Master acquisition/materialization. `manage_security_master.py update --live` selects the formal release root through `--root`, while it discovers input bundle snapshots under `REPO_ROOT/data/security_master/input_bundles`. The materializer itself writes raw payloads, candidate artifacts, and reports beneath `ROOT/data/security_master/input_bundles` and checkout-local review paths. These are acquired source artifacts and governed provenance, not merely disposable cache. A future contract must bind acquisition staging and retained bundle placement to the selected installation state, distinguish transient staging from retained source artifacts, and leave explicit update as the only acquisition trigger. `start`, future `init`, and `doctor` must never acquire market/source data.

The minimum Native packaging recommendation for later Owner decision is a versioned application bundle with an isolated virtual environment and external durable installation state. It meets replaceability and arbitrary-path goals with less machinery than a wheel/frozen binary/MSI. This is a recommendation, not a frozen choice or implementation authorization. Docker remains a separate Local Service packaging profile: Windows host retains stdio MCP/Agent integration; a container runs only Local Service and mounts explicit durable state. Docker is not implemented here.

## Portability and next boundary

The current evidence does not establish product acceptance for P1-P6. P1/P2 have partial bounded path/config seams; P3-P6 remain gaps or not-yet-implemented. The detailed P1-P6 matrix, root/config matrices, lifecycle analysis, Docker boundary, reuse map, decision ledger, and candidate exit criteria are in this run's machine-readable artifacts.

Recommended sequence, subject to new authorization: A1 installation identity/state/configuration contract; A2 native installation/lifecycle integration; A3 versioned Native application distribution; A4 Docker Local Service packaging; A5 integrated P1-P6 portability acceptance; A6 technical exit review. The sequence does not authorize any tranche.

`COMPLETE` means the current state and contract gaps are inventoried sufficiently to plan a bounded next tranche. It does not mean portability is implemented or accepted. No runtime/product, state, dependency, schema, Catalog, Route, executor/source, Docker, installer, or `init` implementation changed. No live acquisition or provider request occurred.
