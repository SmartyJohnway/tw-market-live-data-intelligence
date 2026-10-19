"""Acceptance-only deterministic assembler for the L5-A1 governance evidence package."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "l5-a1-20261018T140202Z"
RUN = ROOT / "docs/governance/phase_l/acceptance_runs" / RUN_ID
A0 = ROOT / "docs/governance/phase_l/acceptance_runs/l5-a0-20261018T110810Z"
R1 = ROOT / "docs/governance/phase_l/acceptance_runs/l5-a0-r1-20261018T122006Z"
BASE = "0a1b3bf3b18b009cc8f54c6207a468612d337f9f"
TREE = "efacdd6ac413bce4f2238be61344171f7639780e"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def canonical_bytes(raw: bytes) -> bytes:
    return raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def verify_manifest(path: Path, expected: str, historical_commit: str | None = None):
    manifest = load(path)
    digest = manifest.pop("manifest_canonical_sha256")
    actual = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == expected == actual, (path, digest, actual)
    historical = []
    for item in manifest["artifacts"]:
        data = canonical_bytes((ROOT / item["path"]).read_bytes())
        if len(data) != item["canonical_bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            assert historical_commit, item["path"]
            committed = subprocess.run(["git", "show", f"{historical_commit}:{item['path']}"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
            committed = canonical_bytes(committed)
            assert len(committed) == item["canonical_bytes"] and hashlib.sha256(committed).hexdigest() == item["sha256"], item["path"]
            historical.append({"path": item["path"], "verified_at_commit": historical_commit, "current_difference": True})
    return {"path": path.relative_to(ROOT).as_posix(), "artifact_count": manifest["artifact_count"], "manifest_canonical_sha256": digest, "all_member_hashes_verified": True, "members_verified_from_historical_commit": historical}


OWNERS = {
    "DIM-01": ("Existing typed evidence contract/schema authority; source versions remain distinct.", "Typed evidence schema/family contract owner."),
    "DIM-02": ("Unified Capability Catalog authority.", "Unified Capability Catalog version authority."),
    "DIM-03": ("Unified Capability Catalog and installation-local identity validator.", "Catalog and routing authority as applicable."),
    "DIM-04": ("Frozen Unified Request schema/version authority.", "Unified Request resolver and preferred request-version authority."),
    "DIM-05": ("Unified Capability Catalog bounds and request validator.", "Catalog and request validator authority."),
    "DIM-06": ("Existing source authority and family source contracts.", "Family source contract/source authority owner."),
    "DIM-07": ("Routing matrix, executor metadata, and trusted callable binding.", "Routing matrix and executor registry authorities."),
    "DIM-08": ("Routing matrix and executor metadata; network boundary is platform-owned.", "Routing/executor metadata and L4 platform policy."),
    "DIM-09": ("Typed family evidence contract and source semantic validator.", "Typed evidence schema owner; source contract separately versioned."),
    "DIM-10": ("Existing adapter timing and operation/Result semantics.", "Result/operation evidence version owner; timing is governed by L1."),
    "DIM-11": ("Existing currentness contract/resolver and Catalog timing classes.", "Family/currentness contract; Catalog only when advertised behavior changes."),
    "DIM-12": ("Typed family evidence semantics and Result projection.", "Typed family evidence and Result owners as public shape requires."),
    "DIM-13": ("Unified capability/request validator and unsupported reason mapping.", "Unified Request/Catalog compatibility owner."),
    "DIM-14": ("Source contract and bounded adapter failure mapping.", "Source contract and existing Result/Audit owners."),
    "DIM-15": ("Canonical receipt, lineage, and Audit authority.", "Audit package schema/version owner."),
    "DIM-16": ("Canonical citation builder and governed lineage identity.", "Citation/provenance owner; handoff owner only if public envelope changes."),
    "DIM-17": ("Existing test files and explicit execution profile registration.", "Test profile/config and conformance acceptance authority."),
    "DIM-18": ("Unified Capability Catalog and synchronized portable output checks.", "Catalog version authority."),
    "DIM-19": ("Current runtime Skill/guide and synchronization validator.", "Current Skill/guide publication owner."),
    "DIM-20": ("Owner-controlled family acceptance ledger.", "Owner acceptance authority."),
    "DIM-21": ("Subordinate operation-evidence schema and applicable retention policy.", "Subordinate evidence schema owner; L2 retention authority."),
    "DIM-22": ("Existing replay inspector and explicit artifact compatibility declarations.", "Existing replay contract and L2 compatibility authority."),
    "DIM-23": ("Existing canonical Audit package builder; derived projection.", "Audit schema/version owner."),
    "DIM-24": ("Existing canonical Unified Mode C handoff builder; derived projection.", "AI handoff/service envelope owner."),
    "DIM-25": ("Accepted family/source contract and trusted source adapter.", "Family/source contract owner."),
    "DIM-26": ("Accepted typed family contract and deterministic normalizer.", "Typed evidence schema/family contract owner."),
    "DIM-27": ("Installation-local Taiwan Market Identity Service.", "Installation-local identity authority; no family version fork."),
    "DIM-28": ("Existing Unified Result projection and frozen schema authority.", "Unified Result schema/version owner."),
    "DIM-29": ("Platform Mode B authorization and execute-once controls.", "Platform authorization authority."),
    "DIM-30": ("Platform executor metadata and finite timeout policy.", "Executor metadata/platform timeout authority."),
    "DIM-31": ("Platform L2 retention inventory and accepted policy.", "Platform L2 retention authority."),
    "DIM-32": ("Shared platform resource-boundary authorities.", "Platform resource policy owner."),
    "DIM-33": ("Platform local network/control-plane secret boundary.", "Platform security/network-boundary owner."),
    "DIM-34": ("Platform filesystem/output containment utilities.", "Platform filesystem-safety policy owner."),
    "DIM-35": ("Explicit mappings across current namespaces; no family registry.", "No new version boundary; existing typed and public authorities own transitions."),
    "DIM-36": ("Existing version authority for each affected boundary.", "Existing boundary owners in T1-T12; no new versioning system."),
}


def applicability(name: str, finding_id: str) -> str:
    if finding_id == "DIM-35":
        return "Always applicable as a governance mapping; declare each existing identity namespace separately."
    if finding_id == "DIM-36":
        return "Always applicable; classify every affected boundary for each change."
    if name in {"network-required flag", "source timestamp semantics", "source authority", "source request contract", "source failure semantics"}:
        return "Declare APPLICABLE for source-backed acquisition; local/derived families may declare NOT_APPLICABLE only with evidence that no source acquisition occurs."
    if name == "identity binding":
        return "Applicable for target-bound evidence. Otherwise NOT_APPLICABLE requires explicit no-target scope and identity-independent contract proof."
    if name == "raw evidence schema":
        return "OPTIONAL: declare a schema or explicitly declare none. NOT_APPLICABLE only when no raw/operation artifact is emitted or retained."
    if name == "replay support":
        return "OPTIONAL: declare supported or unsupported. Unsupported is not NOT_APPLICABLE and never implies refetch."
    if name in {"Catalog publication", "Skill/guide publication"}:
        return "Applicable when public support/usage changes; NOT_APPLICABLE requires proof that no public behavior or user guidance changes."
    if name == "retention classification":
        return "Mandatory for persistent artifacts; NOT_APPLICABLE only when no persistent artifact exists and this is proven."
    return "Every family states APPLICABLE or NOT_APPLICABLE with rationale and evidence; omission is invalid. Default to APPLICABLE when the corresponding boundary exists."


def acceptance(name: str) -> str:
    specific = {
        "tests": "Deterministic unit/contract tests and required offline validators, with evidence for declared semantics.",
        "Catalog publication": "Catalog contract validation and portable Catalog synchronization checks.",
        "Skill/guide publication": "Runtime Skill/guide synchronization check and bounded user guidance.",
        "acceptance authority": "Owner acceptance ledger binds contract versions, registrations, and evidence hashes.",
        "identity binding": "Canonical ISIN/MARKET:CODE target tests and proof there is no alternate identity authority.",
        "source authority": "Source-contract validation, bounded fixtures, provenance, and applicable source-drift cases.",
        "parameter bounds": "Request validator tests accepted limits and fail-closed over-bound inputs.",
        "source failure semantics": "Failure matrix preserves source-failed vs missing/unsupported/stale distinctions.",
        "freshness/currentness semantics": "Fixtures keep source, publication, retrieval, and observed time distinct.",
        "provenance requirements": "Operation/artifact lineage and canonical Audit construction validation.",
        "citation requirements": "Citation index resolves to exact retained operation/evidence lineage.",
        "Result projection": "Unified Result schema validation and compatibility checks for its declared version.",
        "Audit projection": "Canonical Audit schema and lineage checks; no parallel audit path.",
        "AI handoff projection": "Existing handoff validation/render checks and cited Result/Audit compatibility.",
        "replay support": "Replay inspector fixtures distinguish READ_EXISTING, REFETCH, and unsupported replay.",
        "raw evidence schema": "Strict subordinate schema validation and L2 role/retention classification when retained.",
        "authorization class": "Mode B preview/authorization/execute-once tests; preview never implies approval.",
        "timeout authority": "Finite timeout authority and bounded-call tests in platform executor metadata.",
        "retention classification": "L2 classification and backup/restore/compatibility evidence; no family policy.",
        "resource bounds": "L4 input/output/artifact/memory/disk/concurrency boundary tests.",
        "secret boundary": "Credential-free configuration and secret/log redaction boundary review.",
        "path/output containment": "Contained output tests for traversal, links/reparse, atomic output, and quota cases.",
    }
    return specific.get(name, "Accepted contract/schema conformance tests with deterministic evidence at the owning authority seam.")


def build_dimensions(a0_contract):
    result = []
    for d in a0_contract["findings"]:
        fid, name = d["finding_id"], d["dimension"]
        old = d["classification"]
        cls = "REQUIRED" if fid in {"DIM-35", "DIM-36"} else old
        owner, version_owner = OWNERS[fid]
        surfaces = {x["path"] for x in d.get("exact_source_files", [])}
        if d.get("current_authority"):
            surfaces.add(d["current_authority"])
        result.append({
            "dimension_id": fid, "name": name, "classification": cls,
            "classification_before_a1": old, "applicability_rule": applicability(name, fid),
            "declarer": "Extension proposer and author of accepted family/source contract; Owner confirms completeness.",
            "canonical_owner": d.get("current_authority"), "canonical_owner_role": owner,
            "registration_surface": sorted(surfaces), "version_owner": version_owner,
            "acceptance_evidence": acceptance(name),
            "not_applicable_rule": "Only explicit NOT_APPLICABLE with bounded scope, rationale, and evidence that the underlying concept/operation/artifact does not exist. Absence never means N/A.",
            "source_finding_id": fid,
            "evidence_files": [x["path"] for x in d.get("exact_source_files", [])],
        })
    counts = {k: sum(x["classification"] == k for x in result) for k in ["REQUIRED", "OPTIONAL", "DERIVED", "FAMILY_SPECIFIC", "PLATFORM_PROVIDED", "DECISION_REQUIRED"]}
    assert len(result) == 36 and counts == {"REQUIRED": 22, "OPTIONAL": 2, "DERIVED": 2, "FAMILY_SPECIFIC": 4, "PLATFORM_PROVIDED": 6, "DECISION_REQUIRED": 0}, counts
    return result, counts


def build():
    RUN.mkdir(parents=True, exist_ok=True)
    assert not any(RUN.iterdir()), "A1 run directory must be empty before assembly"
    a0v = verify_manifest(A0 / "manifest.json", "aa7dee61185eddb66e4adb5c08b700fb884404dbf77e26ba6187a1097277ba94")
    r1v = verify_manifest(R1 / "manifest.json", "c3975ce5726182b2d831d9c9b82ff3a300912a7222a536665a1acb9985d9a78f", "05971acf4484604307b3d016c667c64515de42fd")
    a0 = load(A0 / "candidate_minimum_extension_contract.json")
    reginput = load(A0 / "extension_registration_surface_inventory.json")
    assert len(reginput["findings"]) == 39 and load(A0 / "offline_review.json")["status"] == "INTERNALLY_COMPLETE_FOR_FRONT_DOOR_TRANSITION"
    assert load(A0 / "architecture_conflict_register.json")["architecture_conflict_count"] == 0
    assert load(A0 / "plugin_framework_need_assessment.json")["assessment"] == "PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW"
    rows, counts = build_dimensions(a0)
    contract = {
        "contract_id": "L5_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT", "contract_version": "1",
        "authority_kind": "GOVERNANCE_ARCHITECTURE_CONTRACT_ONLY", "status": "TECHNICAL_FREEZE_CANDIDATE",
        "technical_disposition": "L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_TECHNICAL_FREEZE_PASS",
        "owner_acceptance": "PENDING", "not_a_runtime_registry": True, "not_a_public_product_schema": True,
        "not_a_plugin_manifest": True,
        "scope": "Minimum declaration, ownership, registration, versioning, applicability, and conformance proof for a future evidence family. No family is added or activated.",
        "namespace_policy": {
            "universal_family_id_registry": "PROHIBITED_FOR_CURRENT_ARCHITECTURE",
            "evidence_family_identity": "Architecture/conformance concept established by explicit mappings across existing authorities.",
            "namespaces": {
                "capability_id": "Public request/data_need intent and parameters; Unified Request and canonical Capability Catalog.",
                "typed_evidence_contract_id": "Normalized evidence semantics/version; existing typed schema and accepted family contract.",
                "source_contract_id": "Provider/dataset/request-response acquisition semantics; existing source contract/authority.",
                "source_authority_identity": "Approved source identity and activation; existing source authority.",
                "executor_id": "Trusted implementation identity; current executor metadata and closed callable binding.",
                "routing_identity": "Existing Request planning authority plus capability/market/target route and output binding; current routing matrix/resolver.",
            },
            "cardinality_rules": {
                "capability_to_typed_evidence_contract": "N:M explicitly permitted; one contract may support multiple capabilities and one capability may compose multiple contracts.",
                "typed_evidence_to_source_contract": "N:M explicitly permitted; multiple source contracts can normalize to one stable typed contract and one source may feed multiple projections.",
                "capability_to_executor": "N:M across product; each resolved context selects exactly one trusted executor; blocked/contract-only contexts may select zero.",
                "source_to_executor": "N:M across product; actual bounded binding is explicit.",
                "mapping_rule": "No mapping inferred from names or 1:1 assumptions; never collapse namespaces or add a second registry.",
            },
        },
        "applicability_policy": {
            "required_for_every_dimension": "Every family records APPLICABLE or NOT_APPLICABLE for all 36 dimensions. Optional raw/replay features also explicitly say supported/provided or unsupported/not provided.",
            "omission": "Invalid; absence never implies no network, retention, replay, timeout, authorization, or identity binding.",
            "not_applicable": "Requires scope, rationale, and evidence; cannot avoid an existing platform control.",
            "local_derived": "May mark network transport N/A only when no source acquisition occurs; execution, identity, retention, path, and resource boundaries still require explicit assessment.",
        },
        "dimensions_input_count": 36, "dimensions_frozen_count": 36, "dimensions_dropped_count": 0,
        "unexplained_new_dimensions_count": 0, "classification_counts": counts, "dimensions": rows,
        "registration_policy": "Use existing authorities. Preserve intentional independent checks and synchronized views; no dynamic discovery or new family registry.",
        "version_transition_authority": "T1-T12 and VER-01..VER-08 in the A1 run; each transition is conditional on its stated change.",
        "deprecation_policy": [
            "Deprecation is explicit governance state, not deletion.",
            "Historical retained artifacts remain readable under their declared version or fail closed explicitly.",
            "A deprecated identity never silently points to new semantics.",
            "Source deprecation never rewrites historical provenance.",
            "Removal, migration, or compatibility break requires separate Owner authorization.",
        ],
        "cross_phase_inheritance": "Every family inherits L1 operability, L2 replay/retention/migration classification, L3 applicable source drift, and L4 security/resource controls.",
        "conformance_proof_classes": ["identity/capability mapping", "source authority", "typed contract/schema validation", "normalization determinism", "timing/currentness", "missing/unsupported/failure separation", "provenance/citations", "Result projection", "Audit/handoff compatibility", "L1-L4 inheritance", "Catalog/route/Skill synchronization where applicable", "bounded offline regression", "Owner acceptance"],
        "plugin_framework_assessment": "PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW",
        "negative_invariants": ["No universal runtime family registry merely for extensibility.", "No second Catalog/source/executor/identity authority, request protocol, or Result/Audit system.", "No family-specific MCP tool.", "No dynamic third-party execution, Python entry points, discovery, or hot loading.", "No hidden acquisition or automatic source/capability activation.", "No trading, order routing, or broker credentials."],
        "evidence_change_boundary": {"production_runtime_changes": 0, "public_mcp_changes": 0, "catalog_capability_changes": 0, "routing_activation_changes": 0, "executor_activation_changes": 0, "source_activation_changes": 0, "new_evidence_schema_activation": 0, "unified_request_semantic_changes": 0, "unified_result_semantic_changes": 0, "audit_semantic_changes": 0, "dependency_changes": 0, "production_state_mutations": 0},
    }
    dump(ROOT / "docs/governance/phase_l/PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT.v1.json", contract)
    dump(RUN / "minimum_extension_contract_matrix.json", {"input_dimension_count": 36, "frozen_dimension_count": 36, "dropped_dimension_count": 0, "unexplained_new_dimension_count": 0, "remaining_decision_required": 0, "classification_counts": counts, "dimensions": rows})

    ex = [
        {"capability_id": "monthly_revenue", "typed_evidence_contract_id": "monthly_revenue_evidence.v1", "operation_evidence_contract_id": "phase_g_monthly_revenue_operation_evidence.v1", "source_contract_ids": ["t187ap05_L", "t187ap05_O"], "source_authority_identity": "MOPS_MONTHLY_REVENUE_OPEN_DATA", "executor_id": "phase_g_official_research_executor", "routing_identity": ["Unified Request V3 / monthly_revenue / TWSE / phase_g_official_research_executor", "Unified Request V3 / monthly_revenue / TPEX / phase_g_official_research_executor"], "public_request_data_need": "data_needs[].capability_id = monthly_revenue", "cardinality": {"capability_to_typed_evidence": "1:1 in this example; N:M permitted", "source_contracts_to_typed_evidence": "N:1", "executor_to_capabilities": "1:N"}, "authority_files": ["schemas/monthly_revenue_evidence.v1.schema.json", "schemas/phase_g_monthly_revenue_operation_evidence.v1.schema.json", "scripts/phase_g/research_executor.py", "scripts/phase_g/mops_monthly_revenue.py", "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json", "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json", "config/m8r_06_03_executor_registry_metadata.json"]},
        {"capability_id": "material_disclosures", "typed_evidence_contract_id": "material_disclosure_evidence.v1", "operation_evidence_contract_id": "phase_g_material_disclosure_operation_evidence.v1", "source_contract_ids": ["t187ap04_L", "t187ap04_O"], "source_authority_identity": "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA", "executor_id": "phase_g_official_research_executor", "routing_identity": ["Unified Request V3 / material_disclosures / TWSE / phase_g_official_research_executor", "Unified Request V3 / material_disclosures / TPEX / phase_g_official_research_executor"], "public_request_data_need": "data_needs[].capability_id = material_disclosures", "cardinality": {"capability_to_typed_evidence": "1:1 in this example; N:M permitted", "source_contracts_to_typed_evidence": "N:1", "executor_to_capabilities": "1:N"}, "authority_files": ["schemas/material_disclosure_evidence.v1.schema.json", "schemas/phase_g_material_disclosure_operation_evidence.v1.schema.json", "scripts/phase_g/research_executor.py", "scripts/phase_g/mops_material_disclosures.py", "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json", "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json", "config/m8r_06_03_executor_registry_metadata.json"]},
        {"capability_id": "market_state_context", "typed_evidence_contract_id": "market_state_context_evidence.v1", "source_contract_ids": ["TWSE_FMTQIK_OPENAPI_V1", "TWSE_TWTAZU_OD_OPENAPI_V1", "TPEX_MAINBORAD_HIGHLIGHT_OPENAPI_V1"], "source_authority_identity": "phase_i_i1_source_authority.v1.json: I1-TWSE-FMTQIK-OPENAPI, I1-TWSE-BREADTH-TWTAZU-OPENAPI, I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI", "executor_id": "phase_i_i1_market_state_executor", "routing_identity": "Unified Request V3 / market_state_context / selected phase_i_i1_market_state_executor", "public_request_data_need": "data_needs[].capability_id = market_state_context", "cardinality": {"capability_to_typed_evidence": "1:1 in this composite example", "source_contracts_to_typed_evidence": "N:1", "executor_to_capabilities": "1:1 for current selected route"}, "authority_files": ["docs/data_capabilities/phase_i_i1_source_authority.v1.json", "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json", "schemas/unified_market_evidence_result.v3.schema.json"]},
    ]
    dump(RUN / "identity_namespace_relationship_decision.json", {"decision": "EVIDENCE_FAMILY_IS_A_CONFORMANCE_CONCEPT_NO_UNIVERSAL_ID", "universal_family_id_required": "NO", "namespaces": contract["namespace_policy"]["namespaces"], "cardinality_rules": contract["namespace_policy"]["cardinality_rules"], "examples": ex, "mapping_rule": "Mappings are explicit in existing authorities; H4 discontinuity_safety is derived and is not a request capability."})

    b = ["source_contract", "evidence_contract", "catalog", "routing", "unified_request", "unified_result", "audit", "ai_handoff"]
    N, Y, M = "MUST_NOT_MOVE", "MAY_MOVE", "MUST_MOVE"
    trans = {
        "T1": ([Y,N,N,Y,N,N,N,N], "Source implementation may move its source contract; route only if binding changes. Prove normalized semantic equivalence."),
        "T2": ([M,N,N,Y,N,N,N,N], "Endpoint/response changes move source contract; route only if binding changes. Prove semantic equivalence."),
        "T3": ([Y,M,Y,M,N,Y,Y,Y], "New optional normalized field gets a new evidence version; route binds it before emission. Catalog and public projections move only for companion behavior/shape changes."),
        "T4": ([Y,M,M,M,M,M,M,Y], "Incompatible evidence requires a new evidence version and explicit read policy. Public capability/request semantics move only under their own version decision; preserve old bytes or fail closed."),
        "T5": ([Y,M,N,M,N,Y,Y,N], "New typed family behind unchanged public intent gets a new evidence identity and explicit route. Result/Audit may move only if public shapes change."),
        "T6": ([Y,M,M,M,M,Y,Y,Y], "New public data_need requires new Catalog and Request versions because V3 vocabularies are closed. Source/evidence/route apply where relevant; projections move only if needed."),
        "T7": ([Y,N,Y,M,N,N,N,N], "Route moves. Source or Catalog moves only if source binding or advertised support changes; evidence and public contracts remain stable."),
        "T8": ([N,N,N,N,N,M,M,Y], "Public Result shape moves Result; Audit moves because it binds Result identity; handoff only if its envelope changes."),
        "T9": ([N,N,N,N,N,N,M,Y], "Public Audit shape moves Audit; handoff only if envelope changes."),
        "T10": ([N,N,N,N,N,N,N,M], "Only the existing public handoff/service contract moves; no per-family handoff version."),
        "T11": ([M,N,Y,Y,N,N,N,N], "Source deprecation is explicit and cannot retarget old identity. Catalog/route move only when support or active binding changes; deprecation is not deletion."),
        "T12": ([N,M,Y,Y,N,N,N,N], "Evidence deprecation is explicit; old identity remains bound to old semantics. Catalog/route move only if support/binding changes; removal is separately authorized."),
    }
    descriptions = ["New source implementation, normalized semantics unchanged", "Endpoint/response changes, normalized semantics unchanged", "Additive optional normalized field", "Incompatible normalized evidence semantics", "New evidence family behind existing public capability", "New public capability/data_need", "Routing/executor binding change", "Result projection shape change", "Audit public shape change", "AI-handoff public envelope change", "Source-contract deprecation", "Evidence-contract deprecation"]
    tr = []
    for i, (vals, rationale) in enumerate(trans.values(), 1):
        tid = f"T{i}"
        tr.append({"transition_id": tid, "change_description": descriptions[i-1], **dict(zip(b, vals)), "compatibility_obligation": rationale, "historical_read_obligation": "Read bytes under declared version or fail closed explicitly; never silently reinterpret.", "acceptance_required": "Yes: compatibility fixtures, relevant validators, updated owner evidence, and explicit Owner acceptance before activation/removal.", "rationale": "Values apply to this transition only; an accompanying change invokes its own row."})
    dump(RUN / "version_transition_matrix.json", {"boundary_values": [M, Y, N], "version_boundaries": b, "transitions": tr, "unresolved_decisions": 0, "version_owners": load(A0 / "versioning_authority_matrix.json")["findings"], "deprecation_policy": contract["deprecation_policy"]})

    regrows = []
    for f in reginput["findings"]:
        regrows.append({"registration_id": f["registration_id"], "finding_id": f["finding_id"], "classification": f["classification"], "canonical_authority": f["current_authority"], "current_behavior": f["current_behavior"], "exact_source_files": [x["path"] for x in f.get("exact_source_files", [])], "a1_rule": "Update this existing authority only when applicable, with coordinated compatibility evidence; never turn it into discovery or a second authority.", "classification_preserved": True})
    dump(RUN / "registration_authority_matrix.json", {"input_surface_count": 39, "registration_surfaces": regrows, "classification_counts": reginput["classification_counts"], "identity_authorities": ["Catalog for capability", "typed schema/family contract for evidence", "source authority for source", "routing matrix/resolver for route", "executor metadata and trusted callable binding for executor"], "no_new_registry": True, "intentional_cross_checks_preserved": True})

    cross = {
        "L1": {"status": "INHERITED_REQUIRED", "requirements": ["Reuse request/operation correlation and execution identity.", "Reuse diagnostics, failure codes, source/adapter timing and network-attempt accounting.", "No second operational truth."], "proof": "One request-to-operation lineage, canonical reason codes, and existing timing/attempt instrumentation."},
        "L2": {"status": "INHERITED_REQUIRED", "requirements": ["Declare artifact roles and READ_EXISTING/replay/refetch distinction.", "Declare replay supported or unsupported; replay is not refetch.", "Classify retention, backup relevance, restore compatibility and migration compatibility."], "proof": "Artifact-role/retention evidence and compatibility fixtures or explicit fail-closed result.", "policy_owner": "Platform L2; no family deletion/retention policy."},
        "L3": {"status": "INHERITED_REQUIRED_WHERE_APPLICABLE", "requirements": ["Network source: transport/status, encoding, parse, schema/field drift, semantic validation, empty response, publication delay, rate limit, removal and contract drift.", "Local/derived: mark transport-only dimensions N/A with proof; semantic validation and provenance remain required."], "proof": "Bounded offline negative fixtures for each applicable drift class and distinct failure/currentness states."},
        "L4": {"status": "INHERITED_REQUIRED", "requirements": ["Loopback/control-plane boundary; path containment; bounded request/output/artifacts.", "Hostile source content remains data; secret and dependency boundaries.", "Finite external timeout, concurrency, dynamic disk admission and memory policy."], "proof": "Existing L4 controls/tests at each exercised seam; family-specific bypass is prohibited.", "policy_owner": "Platform L4, not family."},
        "overall": "Compatibility/conformance requirement only; no future implementation is accepted by A1.",
    }
    dump(RUN / "cross_phase_inheritance_contract.json", cross)
    dump(RUN / "negative_architecture_invariants.json", {"status": "PASS", "invariants": contract["negative_invariants"], "public_mcp_tool_count": 6, "runtime_registry": False, "second_catalog_source_executor_identity_request_or_result_audit_authority": False, "family_owned_platform_policy": False, "dynamic_plugin_loading": False, "new_family": False, "new_capability": False, "frozen_v3_mutation": False})
    dump(RUN / "existing_family_conformance_examples.json", {"examples": ex[:2], "demonstrated": ["Shared executor does not collapse typed evidence or source identities.", "Two market source contracts normalize to one stable typed evidence contract per capability."], "new_family": False, "financial_statements": False})
    dump(RUN / "plugin_framework_assessment.json", {"assessment": "PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW", "basis": ["A0 inventories 39 existing explicit registration responsibilities.", "Trusted callable binding is closed and explicit.", "Current composite/source-backed families are represented by typed evidence contracts and mappings.", "A universal registry duplicates authority and adds unsupported discovery behavior."], "sufficient_model": ["Governance-level declarative typed contract", "Existing explicit registrations", "Trusted runtime adapter registry", "Acceptance conformance"], "dynamic_discovery_or_third_party_execution": "NOT_REQUIRED_OR_AUTHORIZED"})
    dump(RUN / "architecture_conflict_register.json", {"disposition": "NO_ARCHITECTURE_CONFLICT", "architecture_conflict_count": 0, "conflicts": [], "stop_conditions": {"universal_family_id_required": False, "seventh_mcp_tool_required": False, "frozen_v3_mutation_required": False, "new_family_required": False, "dynamic_plugin_loading_required": False, "canonical_authority_conflict": False, "l6_decision_required": False, "owner_decision_unresolved": False}})
    dump(RUN / "a0_input_integrity.json", {"entry_head": BASE, "entry_tree": TREE, "a0_primary_disposition": "L5_A0_EVIDENCE_FAMILY_EXTENSION_SURFACE_INVENTORY_COMPLETE", "a0_manifest": a0v, "a0_r1_manifest": r1v, "dimension_count": 36, "registration_surface_count": 39, "a0_plugin_assessment": "PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW", "protected_inputs": ["A0 run/manifest", "A0-R1 run/manifest", "frozen L0", "L1-L4 closure evidence"], "preservation": "Both manifests and all listed artifact hashes verified before A1 evidence generation; no protected authority is modified."})
    dump(RUN / "preflight_result.json", {"run_id": RUN_ID, "owner_authority": "USER_CHAT_2026-10-18_PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_FREEZE_AUTHORIZATION", "origin_main_head": BASE, "origin_main_tree": TREE, "branch": "phase-l/l5-a1-minimum-extension-contract-freeze", "entry_clean": True, "a0_owner_accepted_merged": True, "a0_merge": "241a5249987c008a28d959677704eee483a1c216", "a1_authorized": True, "a2_plus_authorized": False, "l6_l7_authorized": False, "new_family_implementation": False, "live_acquisition": False})
    dump(RUN / "offline_validation.json", {"status": "PENDING_VALIDATION", "required_checks": ["verify_dependency_supply_chain", "verify_environment", "pip check", "validate_source_registry", "validate_portable_catalog_sync", "validate_runtime_skill_guide_sync", "validate_v1_public_contracts", "validate_unified_market_evidence_contracts", "validate_phase_h_v3_contracts", "compileall", "git diff --check"], "provider_requests": 0, "live_market_source_acquisition": 0, "production_state_mutations": 0, "external_socket_attempts": 0, "external_socket_scope": "No OS-wide monitor; listed checks are offline and no acquisition command is included."})

    md = f"""# Phase L5-A1 — Minimum Evidence-Family Extension Contract (2026-10-18)\n\nStatus: **TECHNICAL CONTRACT FREEZE COMPLETE / OWNER ACCEPTANCE PENDING**. Disposition: `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_TECHNICAL_FREEZE_PASS`. This document and its companion JSON are governance/architecture authorities only, not runtime registry, public schema, plugin manifest, or activation.\n\nOwner authority: `USER_CHAT_2026-10-18_PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_FREEZE_AUTHORIZATION`. Entry main/tree: `{BASE}` / `{TREE}`; branch `phase-l/l5-a1-minimum-extension-contract-freeze` began clean. L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`.\n\nHighest authority is frozen L0, `PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`: define the minimum family extension contract before considering a plugin framework; do not add a family merely to prove architecture. The accepted flow remains source inventory → source contract → capability → schema → adapter → normalization → timing/currentness → Result projection → tests → Skill/guide → acceptance.\n\n## Identity and cardinality\n\nNo universal runtime `family_id` or extension registry is required. “Evidence family” is a conformance concept. Capability/data_need, typed evidence contract, source contract/source authority, executor identity, and routing identity remain separate namespaces with existing owners. Explicit mappings may be N:M: one typed contract may serve multiple capabilities; a capability may compose multiple typed contracts; multiple source contracts may normalize to one stable contract. Each resolved routing context selects exactly one trusted executor; blocked/contract-only contexts may select none. Names never establish mappings. Monthly revenue and material disclosures share the trusted research executor while retaining distinct typed evidence and market source contracts; `market_state_context` composes three source contracts. H4 remains derived, not a request capability. Full identifiers are in the A1 identity evidence.\n\n## Minimum contract\n\nAll 36 A0 dimensions are resolved one-for-one: **22 REQUIRED, 2 OPTIONAL, 2 DERIVED, 4 FAMILY_SPECIFIC, 6 PLATFORM_PROVIDED, 0 DECISION_REQUIRED**. Each dimension records applicability, declarer, canonical owner, registration surfaces, version owner, acceptance proof, and a NOT_APPLICABLE rule in [the frozen candidate JSON](PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT.v1.json). No dimensions were dropped or added. Every family declares APPLICABLE or NOT_APPLICABLE with rationale and evidence; omission never implies no network, retention, replay, timeout, authorization, or identity binding. Optional raw evidence and replay must be declared; replay is distinct from refetch. Audit and handoff derive from canonical authorities. Family-specific semantics cannot override platform policy.\n\nThe 39 A0 registration responsibilities remain in their existing Catalog, schema, source, routing, executor, planner, callable, test, guide, synchronized-view, and Owner-acceptance surfaces. Intentional cross-checks remain. No new registry or dynamic discovery is introduced.\n\n## Versioning, deprecation, and L1-L4\n\nT1-T12 resolve the eight existing version boundaries. `MUST_MOVE`, `MAY_MOVE`, and `MUST_NOT_MOVE` apply to the named transition only; companion changes invoke their own row. Source-only movement preserves normalized semantics only with proof. Additive optional normalized fields use a new evidence-contract version. Frozen Request V3 remains closed; a new public capability requires explicit Catalog and Request version decisions. Result, Audit, and handoff move only when their public shape or compatibility requires it. No per-family handoff version is added.\n\nDeprecation is explicit governance state, not deletion. Old identity stays bound to old semantics; historic bytes remain readable under declared versions or fail closed. Source deprecation never rewrites provenance. Removal or migration requires separate Owner authorization.\n\nL1 reuses correlation, diagnostics, failure codes, timing and network-attempt accounting. L2 requires artifact roles, READ_EXISTING/replay/refetch distinction, retention classification, backup/restore and migration compatibility; policy stays platform-owned. L3 source-drift obligations apply to network-backed sources; local/derived families explicitly mark transport-only items N/A. L4 security/resource controls remain mandatory, including control-plane boundary, containment, bounded inputs/outputs, hostile-source handling, secrets/dependencies, timeout, concurrency, disk and memory policy. The evidence matrix defines proof; it does not accept future implementations.\n\n## Framework and scope\n\n`PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW`: a typed governance contract, existing explicit registrations, trusted adapter binding, and conformance acceptance cover current evidence. A1 changes governance/evidence only. Runtime, MCP, Catalog capabilities, routing/activations, schemas, Request/Result/Audit semantics, dependencies, and production state do not change. Provider requests: 0; live acquisition: 0; production state mutations: 0. No OS-wide network observation is claimed. Front doors record A0 merged, A1 technical freeze complete / Owner acceptance pending, A2+ and L6-L7 not authorized. A1 PASS does not authorize A2.\n"""
    (ROOT / "docs/governance/phase_l/PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_2026-10-18.md").write_text(md, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
