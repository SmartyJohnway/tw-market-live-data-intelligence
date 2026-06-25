import json
import os
import sys
from datetime import datetime, timezone, timedelta

# --- Constants & Static Governance Structures ---

SOURCE_CONTRACT_BASELINE = {
    "canonical_sources": [
        "TWSE_MIS",
        "Yahoo_Finance",
        "TWSE_OpenAPI",
        "TPEx_OpenAPI",
        "FinMind",
        "Fugle",
        "Fubon"
    ],
    "official_eod_sources": [
        "TWSE_OpenAPI",
        "TPEx_OpenAPI"
    ],
    "unofficial_live_candidate_sources": [
        "TWSE_MIS"
    ],
    "third_party_context_sources": [
        "Yahoo_Finance",
        "FinMind"
    ],
    "auth_required_sources": [
        "Fugle",
        "Fubon"
    ],
    "doc_only_sources": [
        "Fugle",
        "Fubon"
    ],
    "unsupported_or_deferred_sources": [],
    "source_contract_caveats": [
        "official_openapi_sources_are_eod_reference_only",
        "twse_mis_is_unofficial_frontend_candidate",
        "third_party_sources_require_caveats",
        "broker_sources_are_auth_required_or_doc_only"
    ]
}

AI_MAY_SAY = [
    "The context pack is bounded to the configured watchlist.",
    "The current snapshot may be an offline failure envelope.",
    "Some sources were unavailable, failed, or not attempted in offline mode.",
    "Official OpenAPI sources are EOD/reference sources only.",
    "TWSE MIS is an unofficial frontend live candidate and must carry caveats.",
    "Yahoo Finance and FinMind are third-party context sources and must carry caveats.",
    "Broker sources are auth_required/doc_only in current repo scope.",
    "Watchlist observations are descriptive only.",
    "Source failures and stale data limit what can safely be summarized."
]

AI_MUST_NOT_CLAIM = [
    "Do not claim full-market coverage.",
    "Do not claim official realtime quotes unless explicitly proven.",
    "Do not claim EOD OpenAPI data is live intraday data.",
    "Do not claim TWSE MIS, Yahoo, or FinMind is official exchange authority.",
    "Do not turn watchlist observations into buy/sell/hold signals.",
    "Do not rank securities as investment opportunities.",
    "Do not infer target prices.",
    "Do not provide execution advice.",
    "Do not hide stale data or source failure caveats.",
    "Do not claim broker-account or authenticated data availability without explicit credentials and scope.",
    "Do not introduce unsupported average-volume, moving-average, momentum, ranking, or trend-strength language unless future artifacts explicitly support it."
]

MANDATORY_CAVEATS = [
    "bounded_watchlist_only",
    "not_full_market_coverage",
    "not_investment_advice",
    "observations_are_not_signals",
    "official_openapi_sources_are_eod_reference_only",
    "twse_mis_is_unofficial_frontend_candidate",
    "third_party_sources_require_caveats",
    "broker_sources_are_auth_required_or_doc_only",
    "failed_sources_and_failed_targets_limit_summary"
]

PROHIBITED_INTERPRETATIONS = [
    "The market is live and 2330 is a buy. The official TWSE feed shows strong momentum across the entire market.",
    "The ETF 0050 has positive momentum and its target price is 150.",
    "These observations indicate a strong sell signal for the target.",
    "Execute a trade now based on this volume trend."
]

# --- Core Functions ---

def load_json(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def write_markdown(pack: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    lines = []
    lines.append("# AI Context Pack v2")
    lines.append("")

    # Metadata
    lines.append("## Generated Metadata")
    lines.append(f"- **Pack version:** {pack.get('pack_version')}")
    lines.append(f"- **Generated at UTC:** {pack.get('generated_at_utc')}")
    lines.append(f"- **Generated at Taipei:** {pack.get('generated_at_taipei')}")
    lines.append(f"- **Generation mode:** {pack.get('generation_mode')}")
    lines.append("")

    # Source Contract Baseline
    lines.append("## Source Contract Baseline")
    scb = pack.get("source_contract_baseline", {})
    lines.append("- **Canonical sources:** " + ", ".join(scb.get("canonical_sources", [])))
    lines.append("- **Official EOD sources:** " + ", ".join(scb.get("official_eod_sources", [])))
    lines.append("- **Unofficial live candidate sources:** " + ", ".join(scb.get("unofficial_live_candidate_sources", [])))
    lines.append("- **Third-party context sources:** " + ", ".join(scb.get("third_party_context_sources", [])))
    lines.append("- **Auth-required sources:** " + ", ".join(scb.get("auth_required_sources", [])))
    lines.append("- **Doc-only sources:** " + ", ".join(scb.get("doc_only_sources", [])))
    lines.append("- **Source contract caveats:**")
    for caveat in scb.get("source_contract_caveats", []):
        lines.append(f"  - {caveat}")
    lines.append("")

    # Source Health Summary
    lines.append("## Source Health Summary")
    shs = pack.get("source_health_summary", {})
    lines.append(f"- **Total sources:** {shs.get('total_sources', 0)}")
    lines.append(f"- **Unavailable or failed sources:** {len(shs.get('unavailable_or_failed_sources', []))}")
    lines.append(f"- **Offline not attempted sources:** {len(shs.get('offline_not_attempted_sources', []))}")
    lines.append("- **Source health caveats:**")
    for caveat in shs.get("source_health_caveats", []):
        lines.append(f"  - {caveat}")
    lines.append("")

    # Source Authority Summary
    lines.append("## Source Authority Summary")
    sas = pack.get("source_authority_summary", {})
    lines.append(f"- **Usable live sources:** {', '.join(sas.get('usable_live_sources', [])) or 'None'}")
    lines.append(f"- **Usable EOD sources:** {', '.join(sas.get('usable_eod_sources', [])) or 'None'}")
    lines.append("- **Source authority caveats:**")
    for caveat in sas.get("source_authority_caveats", []):
        lines.append(f"  - {caveat}")
    lines.append("")

    # Target Support Summary
    lines.append("## Target Support Summary")
    tss = pack.get("target_support_summary", {})
    lines.append(f"- **Bounded watchlist only:** {tss.get('bounded_watchlist_only')}")
    lines.append(f"- **Full market coverage:** {tss.get('full_market_coverage')}")
    lines.append(f"- **Target count:** {tss.get('target_count', 0)}")
    lines.append(f"- **Failed target count:** {tss.get('failed_target_count', 0)}")
    lines.append("- **Target support caveats:**")
    for caveat in tss.get("target_support_caveats", []):
        lines.append(f"  - {caveat}")
    lines.append("")

    # Latest Snapshot Summary
    lines.append("## Latest Snapshot Summary")
    lss = pack.get("latest_snapshot_summary", {})
    lines.append(f"- **Snapshot version:** {lss.get('snapshot_version')}")
    lines.append(f"- **Symbol count:** {lss.get('symbol_count', 0)}")
    lines.append(f"- **Failed symbol count:** {lss.get('failed_symbol_count', 0)}")
    lines.append(f"- **Failed source count:** {lss.get('failed_source_count', 0)}")
    lines.append("")

    # Watchlist Observation Summary
    lines.append("## Watchlist Observation Summary")
    wos = pack.get("watchlist_observation_summary", {})
    lines.append(f"- **Observation version:** {wos.get('observation_version')}")
    lines.append(f"- **Observations count:** {wos.get('observations_count', 0)}")
    lines.append(f"- **Failed observations count:** {wos.get('failed_observations_count', 0)}")
    lines.append("- **Categories present:** " + ", ".join(wos.get("categories_present", [])))
    lines.append("")

    # Failed Sources
    lines.append("## Failed Sources")
    failed_sources = pack.get("failed_sources", [])
    if not failed_sources:
        lines.append("None.")
    for fs in failed_sources:
        lines.append(f"- **{fs.get('source_id')}** ({fs.get('authority_level', 'unknown')})")
        lines.append(f"  - Error type: {fs.get('error_type')}")
        lines.append(f"  - Affected symbol count: {fs.get('affected_symbol_count')}")
    lines.append("")

    # Failed Targets
    lines.append("## Failed Targets")
    failed_targets = pack.get("failed_targets", [])
    if not failed_targets:
        lines.append("None.")
    for ft in failed_targets:
        lines.append(f"- **{ft.get('symbol')}** ({ft.get('target_class', 'unknown')})")
        lines.append(f"  - Reason: {ft.get('failure_reason')}")
    lines.append("")

    # Freshness / Delay / Staleness Summary
    lines.append("## Freshness / Delay / Staleness Summary")
    fds = pack.get("freshness_and_delay_summary", {})
    lines.append(f"- **Stale count:** {fds.get('stale_count', 0)}")
    lines.append(f"- **Unknown freshness count:** {fds.get('unknown_freshness_count', 0)}")
    lines.append(f"- **EOD reference count:** {fds.get('eod_reference_count', 0)}")
    lines.append(f"- **Live candidate count:** {fds.get('live_candidate_count', 0)}")
    lines.append("- **Summary caveats:**")
    for caveat in fds.get("summary_caveats", []):
        lines.append(f"  - {caveat}")
    lines.append("")

    # AI May Say
    lines.append("## AI May Say")
    for rule in pack.get("ai_may_say", []):
        lines.append(f"- {rule}")
    lines.append("")

    # AI Must Not Claim
    lines.append("## AI Must Not Claim")
    for rule in pack.get("ai_must_not_claim", []):
        lines.append(f"- {rule}")
    lines.append("")

    # Mandatory Caveats
    lines.append("## Mandatory Caveats")
    for caveat in pack.get("mandatory_caveats", []):
        lines.append(f"- {caveat}")
    lines.append("")

    # Next Actions
    lines.append("## Next Actions")
    for action in pack.get("next_actions", []):
        lines.append(f"- {action}")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# --- Generators for context pack components ---

def build_source_health_summary(snapshot: dict) -> dict:
    source_health_list = snapshot.get("source_health", [])
    total_sources = len(source_health_list)
    source_ids = []
    unavailable_or_failed_sources = []
    auth_required_sources = list(SOURCE_CONTRACT_BASELINE["auth_required_sources"])
    doc_only_sources = list(SOURCE_CONTRACT_BASELINE["doc_only_sources"])
    offline_not_attempted_sources = []

    for sh in source_health_list:
        sid = sh.get("source_id")
        source_ids.append(sid)
        error = sh.get("error_type")
        if error:
            unavailable_or_failed_sources.append(sid)
            if "offline" in error:
                offline_not_attempted_sources.append(sid)

    return {
        "total_sources": total_sources,
        "source_ids": source_ids,
        "unavailable_or_failed_sources": unavailable_or_failed_sources,
        "auth_required_sources": auth_required_sources,
        "doc_only_sources": doc_only_sources,
        "offline_not_attempted_sources": offline_not_attempted_sources,
        "source_health_caveats": [
            "source_health_summary_describes_local_generated_source_state_only",
            "does_not_claim_current_live_production_source_availability"
        ]
    }

def build_source_authority_summary(snapshot: dict) -> dict:
    return {
        "official_reference": SOURCE_CONTRACT_BASELINE["official_eod_sources"],
        "unofficial_frontend": SOURCE_CONTRACT_BASELINE["unofficial_live_candidate_sources"],
        "third_party": SOURCE_CONTRACT_BASELINE["third_party_context_sources"],
        "broker_authenticated": SOURCE_CONTRACT_BASELINE["auth_required_sources"],
        "usable_live_sources": [],  # Explicitly empty offline
        "usable_eod_sources": SOURCE_CONTRACT_BASELINE["official_eod_sources"],
        "doc_only_sources": SOURCE_CONTRACT_BASELINE["doc_only_sources"],
        "auth_required_sources": SOURCE_CONTRACT_BASELINE["auth_required_sources"],
        "source_authority_caveats": [
            "usable_live_sources_excludes_eod_openapi_and_broker_sources",
            "twse_mis_is_unofficial_frontend",
            "yahoo_finance_and_finmind_are_third_party"
        ]
    }

def build_target_support_summary(snapshot: dict) -> dict:
    targets = snapshot.get("symbols", [])
    failed_targets = snapshot.get("failed_symbols", [])
    target_classes_observed = set()
    target_classes_failed = set()

    target_count = len(targets)
    for sym in targets:
        cls = sym.get("target_class")
        if cls:
            target_classes_observed.add(cls)

    failed_target_count = len(failed_targets)
    for sym in failed_targets:
        cls = sym.get("target_class")
        if cls:
            target_classes_failed.add(cls)
            target_classes_observed.add(cls)

    target_support_caveats = [
        "target_support_summary_describes_support_and_scope_not_market_movement",
        "target_support_summary_must_not_rank_target_classes_or_securities"
    ]
    if failed_target_count > 0:
        target_support_caveats.append("target_classes_include_failed_bounded_watchlist_targets")

    return {
        "target_classes_observed": list(target_classes_observed),
        "target_classes_failed": list(target_classes_failed),
        "target_classes_supported_candidate": [],
        "target_classes_unsupported": [],
        "target_classes_unknown": [],
        "bounded_watchlist_only": True,
        "full_market_coverage": False,
        "target_count": target_count + failed_target_count,
        "failed_target_count": failed_target_count,
        "target_support_caveats": target_support_caveats
    }

def build_latest_snapshot_summary(snapshot: dict) -> dict:
    return {
        "snapshot_version": snapshot.get("snapshot_version"),
        "snapshot_generated_at_utc": snapshot.get("generated_at_utc"),
        "snapshot_generated_at_taipei": snapshot.get("generated_at_taipei"),
        "generation_mode": snapshot.get("generation_mode"),
        "market_session_status": snapshot.get("market_session_status", {}),
        "target_count": len(snapshot.get("symbols", [])) + len(snapshot.get("failed_symbols", [])),
        "symbol_count": len(snapshot.get("symbols", [])),
        "failed_symbol_count": len(snapshot.get("failed_symbols", [])),
        "failed_source_count": len([sh for sh in snapshot.get("source_health", []) if sh.get("error_type")]),
        "global_caveats": snapshot.get("market_session_status", {}).get("caveats", [])
    }

def build_watchlist_observation_summary(observations: dict) -> dict:
    obs = observations.get("observations", [])
    failed_obs = observations.get("failed_observations", [])

    all_obs = obs + failed_obs

    categories_present = set()
    observation_type_counts = {}
    severity_counts = {}

    for o in all_obs:
        obs_type = o.get("observation_type")
        if obs_type:
            categories_present.add(obs_type)
            observation_type_counts[obs_type] = observation_type_counts.get(obs_type, 0) + 1

        sev = o.get("severity")
        if sev:
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "observation_version": observations.get("observation_version"),
        "observations_count": len(obs),
        "failed_observations_count": len(failed_obs),
        "observation_type_counts": observation_type_counts,
        "severity_counts": severity_counts,
        "categories_present": list(categories_present),
        "global_caveats": [
            "observations_are_descriptive_only",
            "observations_are_not_trading_signals"
        ]
    }

def build_failed_sources(snapshot: dict) -> list:
    failed_sources = []

    # Lookup from snapshot.failed_sources
    failed_sources_dict = {}
    for fs in snapshot.get("failed_sources", []):
        failed_sources_dict[fs.get("source_id")] = fs

    for sh in snapshot.get("source_health", []):
        if sh.get("error_type"):
            authority_level = sh.get("authority_level")
            sid = sh.get("source_id")

            # Derive conservatively if not present
            if not authority_level:
                if sid in SOURCE_CONTRACT_BASELINE["official_eod_sources"]:
                    authority_level = "official_reference"
                elif sid in SOURCE_CONTRACT_BASELINE["unofficial_live_candidate_sources"]:
                    authority_level = "unofficial_frontend"
                elif sid in SOURCE_CONTRACT_BASELINE["third_party_context_sources"]:
                    authority_level = "third_party"
                else:
                    authority_level = "unknown"

            fs_lookup = failed_sources_dict.get(sid, {})
            affected_symbols = fs_lookup.get("affected_symbols", [])
            affected_symbol_count = len(affected_symbols) if affected_symbols else 0

            caveats = set(sh.get("caveats", []))
            caveats.update(fs_lookup.get("caveats", []))

            failed_sources.append({
                "source_id": sid,
                "source_type": sh.get("source_type", "unknown"),
                "authority_level": authority_level,
                "error_type": sh.get("error_type"),
                "affected_symbol_count": affected_symbol_count,
                "caveats": list(caveats)
            })
    return failed_sources

def build_failed_targets(snapshot: dict) -> list:
    failed_targets = []
    for f in snapshot.get("failed_symbols", []):
        failed_targets.append({
            "symbol": f.get("symbol"),
            "target_class": f.get("target_class", "unknown"),
            "failure_reason": f.get("failure_reason", "unknown"),
            "source_attempts": f.get("source_attempts", []),
            "caveats": f.get("caveats", [])
        })
    return failed_targets

def build_freshness_and_delay_summary(snapshot: dict) -> dict:
    symbols = snapshot.get("symbols", [])

    freshness_status_counts = {}
    delay_status_counts = {}

    stale_count = 0
    unknown_count = 0
    eod_count = 0
    live_count = 0
    delayed_count = 0

    for sym in symbols:
        freshness = sym.get("freshness_status")
        if freshness:
            freshness_status_counts[freshness] = freshness_status_counts.get(freshness, 0) + 1
            if freshness == "stale": stale_count += 1
            elif freshness == "unknown": unknown_count += 1
            elif freshness == "eod_batch": eod_count += 1
            elif freshness == "delayed": delayed_count += 1
            elif freshness == "realtime_candidate" or freshness == "live": live_count += 1

        delay = sym.get("delay_status")
        if delay:
            delay_status_counts[delay] = delay_status_counts.get(delay, 0) + 1

    summary_caveats = []
    if not symbols and snapshot.get("failed_symbols"):
        summary_caveats.append("latest_snapshot_contains_no_successful_symbols")
        unknown_count = len(snapshot.get("failed_symbols"))
        freshness_status_counts["unknown"] = unknown_count
        delay_status_counts["unknown"] = unknown_count

    return {
        "freshness_status_counts": freshness_status_counts,
        "delay_status_counts": delay_status_counts,
        "stale_count": stale_count,
        "unknown_freshness_count": unknown_count,
        "eod_reference_count": eod_count,
        "live_candidate_count": live_count,
        "delayed_quote_count": delayed_count,
        "summary_caveats": summary_caveats
    }

def build_next_actions(snapshot: dict, observations: dict) -> list:
    actions = []
    if snapshot.get("failed_symbols") or len([sh for sh in snapshot.get("source_health", []) if sh.get("error_type")]):
        actions.append("review_failed_sources_and_targets")
    actions.append("maintain_observational_context")
    return actions

def build_ai_context_pack(snapshot: dict, observations: dict) -> dict:
    now_utc = datetime.now(timezone.utc)
    now_taipei = now_utc.astimezone(timezone(timedelta(hours=8)))

    return {
        "pack_version": "m3_ai_context_pack_v2_draft",
        "generated_at_utc": now_utc.isoformat(),
        "generated_at_taipei": now_taipei.isoformat(),
        "generation_mode": "offline_snapshot_and_observation_read",
        "source_contract_baseline": SOURCE_CONTRACT_BASELINE,
        "source_health_summary": build_source_health_summary(snapshot),
        "source_authority_summary": build_source_authority_summary(snapshot),
        "target_support_summary": build_target_support_summary(snapshot),
        "latest_snapshot_ref": "research/generated/latest_market_snapshot.json",
        "latest_snapshot_summary": build_latest_snapshot_summary(snapshot),
        "watchlist_observations_ref": "research/generated/watchlist_observations.json",
        "watchlist_observation_summary": build_watchlist_observation_summary(observations),
        "failed_sources": build_failed_sources(snapshot),
        "failed_targets": build_failed_targets(snapshot),
        "freshness_and_delay_summary": build_freshness_and_delay_summary(snapshot),
        "ai_may_say": AI_MAY_SAY,
        "ai_must_not_claim": AI_MUST_NOT_CLAIM,
        "mandatory_caveats": MANDATORY_CAVEATS,
        "prohibited_interpretations": PROHIBITED_INTERPRETATIONS,
        "next_actions": build_next_actions(snapshot, observations)
    }

def main():
    snapshot_path = "research/generated/latest_market_snapshot.json"
    observations_path = "research/generated/watchlist_observations.json"

    try:
        snapshot = load_json(snapshot_path)
        observations = load_json(observations_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    pack = build_ai_context_pack(snapshot, observations)

    write_json(pack, "research/generated/ai_context_pack.json")
    write_markdown(pack, "research/generated/ai_context_pack.md")

    print("Successfully generated AI context pack v2 artifacts.")

if __name__ == "__main__":
    main()
