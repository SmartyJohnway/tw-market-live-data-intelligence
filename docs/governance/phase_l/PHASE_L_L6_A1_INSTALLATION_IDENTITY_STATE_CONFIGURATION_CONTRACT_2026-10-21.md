# Phase L6-A1 — Installation Identity / State / Configuration Contract

Technical disposition: `L6_A1_INSTALLATION_IDENTITY_STATE_CONFIGURATION_CONTRACT_FROZEN`

- Phase L6: STARTED
- L6-A0: OWNER-ACCEPTED AND MERGED (PR #397)
- L6-A1: AUTHORIZED; candidate contract technically frozen / Owner acceptance PENDING
- L6-A2+: NOT AUTHORIZED
- Docker implementation: NOT AUTHORIZED
- Installer implementation: NOT AUTHORIZED
- L7: NOT AUTHORIZED
- Phase M: NOT AUTHORIZED

## Authority and exact base

Owner authority: `USER_CHAT_2026-10-21_PHASE_L_L6_A1_INSTALLATION_IDENTITY_STATE_CONFIGURATION_CONTRACT_AUTHORIZATION`. Base `7ec798d682ac91db776608a5e9a6a98e179dd1ec`, tree `a34cb171f206675e1731f8bf7da6c3bcc407c709`, is the normal merge of PR #397. Work is isolated on `phase-l/l6-a1-installation-state-config-contract`; other checkouts/local state remain untouched. Evidence run: `l6-a1-20261021T130000Z`.

This is a contract/governance freeze, not runtime implementation. Owner directs A1-D01-D15; their target contract is formally frozen in this technical candidate, with independent Owner acceptance pending. Existing runtime is not claimed to implement the target.

Inherited frozen authority: L0-D05/D06 application replaceability/state durability; L0-D07 state classes; L0-D08 CLI > ENV > user config > default; L0-D09/D10 lifecycle/explicit migration; L0-D11 backup. Reuse L1 owned-process/read-only doctor, L2 explicit-member backup/isolated restore/migration, L4 path/network/secret/resource boundaries, and L5 exact-six/canonical Catalog/Route/Executor architecture. Historical evidence stays unchanged. L0-D03 remains historical; the accepted prospective policy `USER_CHAT_2026-10-21_WINDOWS11_NATIVE_TIER1_BASELINE_SUPERSESSION` makes Windows 11 x64 the Native Tier-1 baseline from L6 onward.

## Owner-frozen decisions

### A1-D01 — Application/state separation

APP_ROOT is the replaceable, relocatable application/static-resource authority (scripts/server/schemas/Catalog/Route/executor metadata/frontend/skills/VERSION/dependency metadata), never canonical durable state. Durable user/governed state must survive application replacement and must not depend on the application path.

### A1-D02 — TW_MARKET_HOME

TW_MARKET_HOME is the installation control/home authority. Native Windows 11 default is %LOCALAPPDATA%\TW-Market. It is not APP_ROOT, Windows Registry or roaming profile authority.

### A1-D03 — HOME bootstrap precedence

HOME resolves by explicit --home > TW_MARKET_HOME > Windows platform default before reading settings/metadata. settings.json cannot choose its own HOME. No circular dependency or application/developer-path fallback is permitted. Changing HOME selects another installation context; it does not silently copy, adopt or move state. After inherited L4 canonical-path/reparse validation, HOME and STATE_ROOT must not equal APP_ROOT or descend from it; managed durable/governed artifacts must also stay outside the APP_ROOT subtree. APP_ROOT may later be a sibling application directory within HOME if its replacement cannot affect those artifacts; A1 does not freeze A3 packaging placement.

### A1-D04 — TW_MARKET_STATE_ROOT

TW_MARKET_STATE_ROOT defaults to `<HOME>`\state. Fresh init resolves explicit --state-root > TW_MARKET_STATE_ROOT > `<HOME>`\state and persists the resolved absolute state_root in installation metadata. D:\TW-Market-State is an allowed example. For an initialized installation metadata is canonical; conflicting CLI/ENV state-root selection must fail closed without silent relocation. This bootstrap is distinct from ordinary service-setting precedence. Fixed logical subroots are security-master/watchlists/governed, not independent permanent family homes. Canonical state remains outside APP_ROOT.

### A1-D05 — Physical layout and classification

HOME holds meta/config/cache/logs; default STATE_ROOT is HOME/state, or a separately selected root. STATE_ROOT holds security-master/watchlists/governed. %TEMP%\TW-Market\`<installation-id>` holds runtime/temp. Logical class is authoritative irrespective of physical co-location. A retained SM provenance child must be under SM state; exact internal child spelling is not frozen.

### A1-D06 — Installation identity

`<HOME>`\meta\installation.json has minimum logical fields installation_schema_version, installation_id, state_root and created_at. Version must be explicit/supported. installation_id is opaque, generated once during fresh offline init, independent of APP_ROOT, username, machine name and port, and preserved on ordinary init rerun, app upgrade and relocation. UUID encoding is not mandated. P4 restore keeps destination identity; source identity is provenance only. Source PID/ownership and absolute path mapping never become active destination authority. Incompatible metadata fails closed without mutation/migration.

### A1-D07 — Persisted settings authority

`<HOME>`\config\settings.json is the single core persisted user-settings authority: versioned extensible JSON with minimum logical fields schema_version, service.host and service.port. General resolution is explicit CLI > ENV > settings.json > product default. Port: --port > TW_MARKET_PORT > service.port > 8000. Host: --host > TW_MARKET_HOST > service.host > 127.0.0.1, subject to inherited L4 loopback and valid-port bounds. A1 adds no resolver/public schema/Registry/YAML/TOML/dependency. Exact version encoding is a later implementation detail; compatible version recognition is required.

### A1-D08 — Local metadata versus portable preferences

installation.json is local installation identity/path mapping; settings.json carries portable product preferences. Source-machine absolute paths must not be blindly restored as portable preferences. settings cannot override local HOME/state mapping. Existing service-URL integration seam is not a second persisted user-config/home authority.

### A1-D09 — Security Master relocation

`<STATE_ROOT>`\security-master is canonical SM state. Incomplete/unqualified acquisition scratch is ephemeral under %TEMP%\TW-Market\`<installation-id>`\temp\security-master\... or equivalent logical descendant. Final retained official source bundles/provenance are governed logical children of SM state outside APP_ROOT. Rebuildable indexes remain derived even when beside authority today. Explicit SM initialization/update remains the only acquisition path; init/start/doctor/application upgrade never acquire or refresh. Future integration joins manager/loader/materializer selection and explicitly separates staging, qualification, retention and activation. No manager/materializer changes occur here. Finalized retained bundle/report manifests must use installation/state-relative, content-bound identities, never APP_ROOT-dependent absolute paths as portable authority. Only qualified finalized retained state under SM authority may be activation input; ephemeral staging cannot become active/canonical authority. Historical provenance bytes are not rewritten by this future relocation contract.

### A1-D10 — Governed state root

`<STATE_ROOT>`\governed is future canonical installation-relative authority for authorization, claim/control, canonical Results/Audits and associated retained execution evidence. Existing execute-once and Result/Audit/lineage/public contracts remain authoritative. Root selection must reach writers/readers/exporters without a parallel Result/Audit system or historical identity/hash rewrites.

### A1-D11 — Cache/log/runtime/temp split

`<HOME>`\cache is derived/rebuildable and excluded from canonical core backup. `<HOME>`\logs is diagnostic, not Audit truth, excluded from core backup by default; no new duration is frozen and inherited bounded diagnostics remain binding. %TEMP%\TW-Market\`<installation-id>`\runtime holds ephemeral PID/ownership; its temp sibling holds unfinished acquisition/scratch/atomic-operation temporary material. Neither is portable backup content. Installation ID does not replace L1 PID/start-token/executable checks. Existing L2 bounded sibling staging/atomic finalization remains unchanged. No new multi-process/concurrency policy is invented.

### A1-D12 — Offline init responsibility

Future init is explicit, offline and idempotent: resolve HOME; create/read stable identity; resolve/persist state_root; create/verify required layout directories; create/validate versioned settings and metadata; verify local writability/containment; report installation state. Rerun preserves ID/settings/state placement and fails closed on incompatible metadata unless migration is separately authorized. Empty directories do not authorize business/governed records. init cannot acquire data, update/build/qualify/activate SM, restore/migrate, mutate Watchlists, create Result/Audit, authorize execution or repair unrelated state. doctor remains read-only with no implicit init/write probe. No init is implemented.

### A1-D13 — Initialization-state distinction

Future conceptual flow is application available -> INSTALLATION_NOT_INITIALIZED -> explicit offline init -> SECURITY_MASTER_NOT_INITIALIZED -> explicit SM initialization/update -> READY. READY means setup/identity readiness, not market freshness, route activation or execution permission. Current NOT_INITIALIZED is SM state; A2 must expose installation readiness separately while preserving existing-client SM meaning and L1 fresh uninitialized service/diagnostics without acquisition. Missing metadata cannot silently adopt old checkout state. Current runtime codes are unchanged.

### A1-D14 — Legacy root compatibility

Existing root ENV/CLI seams remain. Target chain is HOME -> installation metadata -> STATE_ROOT -> fixed logical subroots. Legacy overrides are not required for P1-P6 acceptance. Future effective roots outside canonical layout must be disclosed as NONCANONICAL_ROOT_OVERRIDE or equivalent typed diagnostic and inherit L4 checks; no silent metadata rewrite/relocation. Exact warning spelling and deprecation/removal timing remain later compatibility/release review.

### A1-D15 — L2 reuse/integration

A1 ownership -> logical member enumeration -> existing L2 backup/restore/migration. Core backup logically includes portable user settings, SM durable authority, Watchlists and required portable facts/pointers. Full governed adds Results/Audits, authorization/control and retained governed provenance. Source ID/runtime/cache/log/temp/absolute path mappings are not portable active authority. L2 remains EXPLICIT_DECLARED_MEMBERS_ONLY, not whole-installation discovery. A1 metadata/settings require later L2 member-family/classification/version adapters; location cannot bypass UNCLASSIFIED_REQUIRES_POLICY. Verified restore is isolated and never activates. MIGRATION_REQUIRED is classification-only; newer unsupported state fails closed; migration is explicit, rollback uses verified A4 retained bytes and replay != refetch. No second backup/migration system.

## Physical ownership and backup mapping

The A1 labels below describe physical ownership roles, not new L2 classification vocabulary. Every backup member still requires explicit family binding/classification; root placement never grants backup tier or retention/deletion eligibility.

| Logical state | Target root | Class | Backup |
|---|---|---|---|
| installation metadata | `<HOME>`\meta\installation.json | INSTALLATION_LOCAL_AUTHORITY | portable facts only; keep destination ID/path mapping |
| persisted user settings | `<HOME>`\config\settings.json | DURABLE_USER_STATE | CORE |
| Security Master authority | `<STATE_ROOT>`\security-master | DURABLE_USER_STATE | CORE |
| retained official SM source/provenance | `<STATE_ROOT>`\security-master\`<logical provenance child>` | GOVERNED_EVIDENCE | FULL_GOVERNED |
| Watchlists | `<STATE_ROOT>`\watchlists | DURABLE_USER_STATE | CORE |
| authorization/claim/Result/Audit/retained execution evidence | `<STATE_ROOT>`\governed | GOVERNED_EVIDENCE | FULL_GOVERNED |
| derived indexes/cache | `<HOME>`\cache | DERIVED_REBUILDABLE | EXCLUDED_CORE |
| operational diagnostics | `<HOME>`\logs | DIAGNOSTIC_NONCANONICAL | EXCLUDED_CORE_DEFAULT |
| PID/ownership | %TEMP%\TW-Market\`<installation-id>`\runtime | EPHEMERAL | EXCLUDED |
| incomplete acquisition/scratch | %TEMP%\TW-Market\`<installation-id>`\temp | EPHEMERAL | EXCLUDED |
| backup output | caller-selected | EXTERNAL_DURABLE_OUTPUT | L2_VERIFIED_BACKUP |
| restore/migration staging | existing L2 bounded caller destination/checkpoint lifecycle | L2_AUTHORITY | existing isolated staging/finalization |

## Existing compatibility seams

| Seam | Classification | Current behavior |
|---|---|---|
| TW_MARKET_SECURITY_MASTER_ROOT | legacy compatibility override | loader/lifecycle ENV or checkout default; manager --root is separate |
| manage_security_master.py --root | narrow operator override | manager explicit root or checkout default |
| TW_MARKET_WATCHLIST_ROOT | legacy compatibility override | Watchlist default_root/production_store |
| M8R_06_03_CONTROL_ROOT | legacy compatibility override | governed producers/readers/Mode B2/Mode C |
| TW_MARKET_OPERATIONAL_EVENT_PATH | diagnostic override | optional bounded operational JSONL sink |
| TW_MARKET_OPERATIONAL_TRACE_ID | diagnostic override | correlation only; not root/installation identity |
| TW_MARKET_HOST / TW_MARKET_PORT | current canonical seam | CLI > ENV > default currently; settings insertion is future |
| UNIFIED_MARKET_EVIDENCE_SERVICE_URL / --service-url | narrow operator override | integration endpoint, not persisted home/config authority |
| M8R_06_03_EXECUTION_ENVIRONMENT / M8R_06_03_TEST_* | test-only seam | acceptance harness, never installation settings |

## P1-P6 implications, not acceptance

- P1 (inherited A0 PARTIAL): New APP_ROOT on same machine preserves HOME/STATE_ROOT/installation ID; application resources remain replaceable.
- P2 (inherited A0 GAP): New Windows user gets user-local HOME and no inherited runtime. Explicit transfer/restore is required where applicable; no old-profile paths.
- P3 (inherited A0 GAP): Fresh Win11 machine/user/arbitrary path uses explicit offline init then explicit SM update. No inherited .git/venv/data/tunnel/developer path.
- P4 (inherited A0 PARTIAL): Destination keeps new installation ID; L2 restores declared portable state into isolated candidate, never source runtime/path activation.
- P5 (inherited A0 PARTIAL): New app inspects supported old state under L2; explicit migration/rollback where required; upgrade is not refresh.
- P6 (inherited A0 NOT_YET_IMPLEMENTED): Logical ownership is container-mappable only. Image/mount/listener/lifecycle syntax and implementation remain A4; portability acceptance A5.

A1 executes no product portability acceptance. P1/P4/P5 remain PARTIAL; P2/P3 remain GAP; P6 remains NOT_YET_IMPLEMENTED.

## Current source mapping and implementation gaps

The target is not implemented today. The following bounded gaps can temporarily remain until separately authorized downstream implementation; none is silently repaired here. Each requires compatibility review; existing-state relocation/adoption is explicit and uses applicable L2 contracts, never hidden init migration.

| Gap | Current source/root | Future surface/tranche |
|---|---|---|
| HOME resolver absent | `scripts/tw_market_lifecycle.py:main`; CLI lacks --home; no persisted home | scripts/tw_market.py; scripts/tw_market_lifecycle.py; shared future resolver; A2 |
| STATE_ROOT resolver absent | `scripts/tw_market_lifecycle.py:_base`; independent per-root ENV/defaults | shared resolver; all root consumers; A2 |
| persisted settings absent | `scripts/tw_market_lifecycle.py:_effective`; CLI > ENV > DEFAULT_HOST/DEFAULT_PORT only | lifecycle/launcher/resolver settings consumers; A2 |
| installation metadata absent | `scripts/tw_market_lifecycle.py:_owner_path`; no installation.json authority | metadata IO/validation and lifecycle identity; A2 |
| SM formal checkout default | `scripts/m8r_08g_security_master_releases.py:SECURITY_MASTER_ROOT; scripts/manage_security_master.py:main; scripts/m8r_06_01c2_mode_a_security_master_loader.py:get_production_mode_a_security_master`; `<APP_ROOT>`/data/security_master; manager --root separate from loader ENV | manager/releases/loader/lifecycle/watchlist SM selection; A2 |
| SM checkout acquisition bundles | `scripts/m8r_06_01b_materialize_production_inputs.py:BUNDLE_BASE; scripts/manage_security_master.py:main`; `<APP_ROOT>`/data/security_master/input_bundles; report paths relative to ROOT | materializer/source bundle retention and manager bundle discovery; A2 |
| checkout-local identity indexes/pointer | `scripts/m8r_06_security_master_candidate_paths.py; scripts/m8r_06_01c2_mode_a_security_master_loader.py:load_mode_a_security_master`; data/security_master/runtime_identity_indexes and config Mode-A pointer | candidate path helpers and legacy loader configuration; A2/A3 |
| Watchlist checkout default | `scripts/m8r_09_persistent_watchlists.py:default_root; scripts/m8r_09_persistent_watchlists.py:production_store`; `<APP_ROOT>`/data/watchlists or TW_MARKET_WATCHLIST_ROOT | Watchlist injection/initialization and consumers; A2 |
| governed checkout default | `server/services/unified_mode_b2.py:CONTROL_ROOT; server/services/unified_mode_c.py:CONTROL_ROOT; scripts/m8r_06_03_execute_once.py`; `<APP_ROOT>`/artifacts/m8r_06_03_workbench or M8R_06_03_CONTROL_ROOT | Mode B2/C; execute-once; retained read/replay/export; physical root injection; A2 |
| checkout-hash runtime identity | `scripts/tw_market_lifecycle.py:_owner_path`; OS temp/tw-market-runtime/<checkout-sha-prefix>/service-<port>.json | L1 lifecycle owner paths; A2 |
| operational event placement | `scripts/tw_market_lifecycle.py:_event_path; server/operational_diagnostics.py:emit_jsonl`; OS temp checkout-hash folder or TW_MARKET_OPERATIONAL_EVENT_PATH | lifecycle child environment + optional diagnostics sink; A2 |
| init command absent | `scripts/tw_market_lifecycle.py:main`; start/status/stop/doctor only | CLI/resolver/metadata/layout validation; A2 |
| NOT_INITIALIZED semantic compression | `scripts/tw_market_lifecycle.py:_sm_status; scripts/manage_security_master.py:main`; SM NOT_INITIALIZED; no installation readiness dimension | readiness/status/doctor and compatibility consumers; A2 |
| legacy root overrides | `scripts/tw_market_lifecycle.py:_base; server/services/unified_mode_c.py; scripts/m8r_09_persistent_watchlists.py:default_root`; existing direct ENV/CLI paths | unified effective-root diagnostics/injection; A2; removal later review |
| L2 A1 settings/metadata integration | `server/services/unified_backup.py:plan_backup; server/services/unified_restore.py:inspect_restore; server/services/unified_migration.py`; explicit declared members; current family/version policy only | logical enumeration + existing L2 classification/compatibility adapter; A2/A5 |
| application/resource lookup remains rooted in source tree | `scripts/tw_market.py:ROOT; scripts/product_version.py:product_version; scripts/m8r_05c/artifact_loader.py:SCHEMAS_DIR`; application-relative imports/resources; VERSION already archive-readable | resource inclusion/layout and no-.git package acceptance; A3 |

Full per-gap compatibility and migration requirements are in `implementation_gap_map.json`. VERSION lookup already works without Git; package resource inclusion and arbitrary-path acceptance remain A3, not A1 implementation.

## A0 reconciliation and explicitly deferred decisions

| A0 decision | Topic | A1 disposition | Authority / boundary |
|---|---|---|---|
| D1 | prospective Windows 11 Tier-1 | OWNER_SUPERSEDED | retained unchanged |
| D2 | installation identity/home | RESOLVED_CONTRACT | A1-D02/D03/D06 |
| D3 | physical state roots | RESOLVED_CONTRACT | A1-D01/D04/D05 |
| D4 | persisted user configuration | RESOLVED_CONTRACT | A1-D07/D08 |
| D5 | SM relocation | RESOLVED_CONTRACT | A1-D09 |
| D6 | control/Result/Audit root | RESOLVED_CONTRACT | A1-D10 |
| D7 | logs/runtime placement | RESOLVED_CONTRACT | A1-D11 |
| D8 | init responsibility | RESOLVED_CONTRACT | A1-D12/D13 |
| D9 | Native packaging | DEFER_A3 | recommendation not frozen |
| D10 | Docker mounts | DEFER_A4 | logical ownership only |
| D11 | Docker lifecycle | DEFER_A4 | not implemented |
| D12 | upgrade/state relationship | ALREADY_FROZEN | L0/L2 retained |
| D13 | P1-P6 strategy | CONTRACT_IMPLICATIONS_ONLY | not acceptance |
| D14 | installer | DEFER_A3_OR_LATER | not selected |
| D15 | release/signing/CI | DEFER_L7 | not selected |

All 15 A1 decisions are OWNER_FROZEN; A1 DECISION_REQUIRED = 0. The five deferred technology/release choices remain outside A1. A0 recommendation of a versioned application bundle plus isolated venv is still a recommendation, not a frozen packaging choice.

## Validation, retained limits and stop boundary

Validation covers exact clean entry, current-source mapping, 15 Owner-frozen decisions, A0 reconciliation, L0/L1/L2/L4/L5 consistency, Windows 11 policy, static exact-six MCP, diff containment and committed-blob manifest integrity. No runtime/product/public schema/dependency or persisted production-state changes occur. No real HOME initialization, restore/migration, Docker daemon/image/build/run or live acquisition is performed.

Full default-ci is not required or rerun for a governance-only freeze. The inherited accepted baseline is 1248 passed / 41 failed / 4 skipped / 5 deselected; the 41 unresolved failures remain failing, not recast as PASS. P1-P6, live-provider certification, new metadata/settings L2 support and physical relocation implementation remain future acceptance obligations.

Provider requests = 0; live acquisition = 0; production user-state mutations = 0; restore/migration execution = 0. Socket measurement, if any, is scoped to its instrumented static-check process, not OS-wide; Git/GitHub repository transport is not provider acquisition.

All content is committed before its manifest is bound. The separate manifest commit hashes the exact committed Git blobs, normalizing UTF-8 CRLF/CR to LF; its deterministic self-hash excludes its own digest field and it is excluded from recursive member hashing. Final member and self-hash verification precedes PR handoff. Historical evidence and Windows prospective policy are byte-preserved.

Stop after PR creation. L6-A1 Owner acceptance is PENDING. L6-A2+, Docker/installer implementation, L7 and Phase M remain NOT AUTHORIZED. Do not auto-merge, self-merge or implement the target contract here.
