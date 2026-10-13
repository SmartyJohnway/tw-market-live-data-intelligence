# Phase L L0 — Production Boundary & Architecture Contract

**Date:** 2026-10-13
**Status:** FROZEN
**Disposition:** `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`
**Parent authority:** Roadmap V3.2 Phase L; Phase K closed under `PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.

## 1. Purpose

Phase L converts the already-correct and agent-portable TW-Market product into a long-term maintainable, portable, upgradeable, diagnosable, extensible, local-first evidence platform.

L0 freezes product and deployment boundaries before implementation. It does not implement L1-L7, add evidence families, reopen Phase J/K acceptance, add a seventh MCP tool, introduce trading/broker semantics, or authorize background polling.

The intended ordinary-user lifecycle is:

```text
obtain TW-Market
→ install
→ initialize
→ start
→ connect an Agent if desired
→ ask a Taiwan-market research question
```

Portability is a first-class product requirement: TW-Market must not depend on the original developer machine, Windows account, checkout path, historical acceptance runtime, or any specific AI host.## 2. Frozen decisions D01-D04

| ID | Frozen decision |
|---|---|
| L0-D01 | Phase L goal is long-term operability, maintainability, portability, extensibility, and releaseability of the existing governed product. |
| L0-D02 | Provisional release target is `v1.5.0`; escalate to `v2.0.0` only when an intentional public or persistent-state breaking change is approved. |
| L0-D03 | Tier-1 Phase L platform targets are Windows 10 x64 and Windows 11 x64. Linux/macOS remain non-blocking unless promoted later. |
| L0-D04 | First-class deployment profiles are Native Windows and Docker Local Service on Windows. Docker is packaging, not a separate product architecture. |

`v2.0.0` escalation includes deliberate removal of supported Request compatibility, incompatible MCP schemas/surface, unreadable historical Result/Audit state, incompatible persistent-state migration without a bridge, or breaking canonical execution semantics.

Native Windows remains the primary operational baseline. The first Docker profile keeps the Windows-host stdio MCP/integration layer and containerizes the Local Service first. Secure Tunnel, DPAPI, and all-in-one container orchestration are not Phase L core dependencies.

## 3. Frozen decisions D05-D06 — portability and state boundary

Portability acceptance covers six distinct cases:

- P1 relocation: same machine, different checkout/install path;
- P2 user portability: different Windows user, no inherited user-local runtime;
- P3 machine portability: different machine and user, fresh clone/download, zero inherited runtime state;
- P4 state portability: restore supported durable state into a new installation;
- P5 upgrade portability: supported old stable state with a newer application;
- P6 Docker portability: fresh supported Docker deployment without developer-machine state.

P3 is the strongest fresh-install requirement: new machine + new Windows user + arbitrary path + clean source/package + zero inherited runtime state must reach install → `NOT_INITIALIZED` → explicit initialize → start → usable.The application/state contract is: **application is replaceable; installation state is durable**. Logical ownership must distinguish application, durable state, cache/derived state, logs, and temporary state even if later packaging maps some of them to shared physical roots.

No product runtime may depend on `D:\Codex-Workspace`, `C:\Users\weitang`, an existing virtual environment, old `data/`, Phase J/K fixtures, Codex/Hermes/Antigravity binaries, or a pre-existing ChatGPT tunnel.

Fresh installation and existing-installation upgrade are separate flows. A fresh installation legitimately begins `SECURITY_MASTER_NOT_INITIALIZED`; upgrade must inspect and preserve supported durable state rather than pretending to be a fresh install.

## 4. Frozen decisions D07-D08 — state and configuration

State classes are:

1. durable user state — Security Master authority, Watchlists, user configuration;
2. governed evidence state — retained Result/Audit/authorization and selected source snapshots/artifacts;
3. derived/rebuildable state — indexes, caches, reproducible projections including AI Handoff unless a release contract explicitly retains it;
4. ephemeral state — temp roots, test roots, scratch material, disposable cache and expired operational logs.

Retention durations and release counts are deliberately not frozen in L0; later evidence must determine them.

Configuration precedence is frozen as:

```text
explicit CLI argument
> environment variable
> user configuration
> product default
```

Windows Registry is not a core configuration authority. `127.0.0.1:8000` remains the default Local Service endpoint, not an immutable canonical identity; supported configuration may change the port without changing product semantics.## 5. Frozen decisions D09-D10 — lifecycle and upgrade promise

Phase L must converge on one user-facing lifecycle entry point. Exact command spelling is deferred, but the product UX must cover at least:

```text
init
start
status
stop
doctor
```

Backup, restore, and migration are also lifecycle responsibilities. Software upgrade and Security Master refresh must remain distinct concepts and commands. `doctor` is read-only by default; repair requires an explicit action. Product startup must not perform hidden market/source acquisition.

Upgrade/migration contract:

- no silent incompatible migration;
- supported state starts normally;
- older-but-migratable state reports `MIGRATION_REQUIRED` rather than mutating silently;
- unsupported or newer state fails closed;
- canonical migration follows inspect → preview → backup → apply → verify;
- rebuildable cache may be regenerated automatically;
- patch releases require no manual state surgery;
- minor releases remain additive/compatible or provide a supported migration;
- major releases may break compatibility only with explicit migration, backup, and release disclosure.

Application rollback may be direct only while state remains backward compatible. An irreversible state migration requires restore from a compatible backup for rollback.

## 6. Frozen decisions D11-D12 — backup and integrations

Core backup covers Security Master durable authority, Watchlists, user configuration, and required persistent pointers/metadata. A full governed backup additionally covers retained Results, Audits, authorization records, and retained source snapshots/artifacts.

Virtual environments, application binaries, Docker images, caches, temporary/test/acceptance runtime, and disposable logs are not canonical backup content.Restore verifies manifest/version/hash where applicable and must not automatically fetch market data, authorize execution, or execute evidence acquisition.

Secure MCP Tunnel, ChatGPT connector, OpenAI Runtime key/DPAPI state, Hermes configuration, Antigravity configuration, Codex, and any specific model/version are optional integration state, not TW-Market core state or backup dependencies.

The canonical relationship is:

```text
TW-Market Core
→ Local Service / local stdio MCP
→ optional Agent integration
```

Agent/source content is data, not control-plane authority: it must not bypass authorization, widen network scope, invent tools, alter canonical Result semantics, or cause evidence text to be interpreted as executable instruction.

## 7. Downstream obligations from the L0 design review

The earlier Phase L design discussion remains binding input and is mapped forward rather than discarded:

- L1 Runtime Operability: lean structured logs; Audit remains governed truth while logs serve diagnosis; request/execution correlation; source/adapter timing; failure codes; bounded resource telemetry; start/stop/status/health/doctor.
- L2 Replay/Retention/Migration: replay old evidence must remain distinct from re-fetch current evidence; retention, backup/restore, hash verification, schema compatibility, migration and rollback.
- L3 Source Drift Hardening: transport → contract → semantic validation; schema/encoding/empty-200/delayed-publication/universe/rate-limit/removal handling; bounded probes, not permanent polling.
- L4 Security & Resource Boundaries: localhost exposure, path containment, input/output limits, prompt/tool-injection boundary, timeouts, memory/disk bounds, and realistic large Watchlist/disclosure/concurrent-Agent cases.
- L5 Extension Architecture: define the minimum evidence-family extension contract before considering any plugin framework; do not add a new family merely to prove the architecture.
- L6 Packaging & Portability: Native Windows plus Docker Local Service, fresh source clone and packaged-install acceptance, machine/user/path/state portability, persistent volume/state contracts.
- L7 CI/Release: deterministic non-network CI, fresh-install profile, bounded live release acceptance, dependency/release manifest, reproducibility, compatibility-range review including the current exact MCP SDK pin, and final stable release decision.Phase L does not introduce `financial_statements`; Roadmap load testing references to a large financial result are interpreted as a **large supported evidence result** unless a future separately authorized capability phase adds financial statements.

## 8. Deliberately deferred implementation values

L0 does not guess operational constants that require implementation evidence. The following remain to be decided in L1-L7:

- physical Windows state/config/log paths;
- exact CLI command spelling and packaging technology;
- retention durations and number of retained rollback releases;
- max targets, evidence rows, payload/artifact sizes, concurrency and timeouts;
- exact resource ceilings;
- exact MCP SDK compatibility range replacing or retaining current exact pinning;
- final `v1.5.0` versus `v2.0.0` release number under D02;
- whether Linux/macOS are later promoted to supported tiers.

These are deferred values, not architecture gaps.

## 9. L0 closure and L1 entry boundary

All L0-D01 through L0-D12 decisions are frozen under:

`PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`

Phase L is now STARTED. No L1 implementation is included in this freeze tranche.

The next authorized planning/implementation boundary is **L1 — Runtime Operability**: inventory existing startup/health/logging/runtime controls, define the minimum product lifecycle surface, and implement only the lean operational substrate needed for start/stop/status/health/doctor and bounded structured diagnostics.

Do not begin L2-L7 implicitly. Do not add new evidence families or broaden live-source activity as part of L1.